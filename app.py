from flask import Flask, render_template, request
import google.generativeai as genai
import os
from dotenv import load_dotenv
import re
import ast


# Load API Key from .env
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize model after configuration
model = genai.GenerativeModel("gemini-1.5-flash")

app = Flask(__name__)

#------------

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/result')
def result():
    return render_template('result.html')

@app.route('/doctor')
def doctor():
    return render_template('doctor.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/blog')
def blog_page():
    return render_template('blog.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/appointment')
def appointment():
    return render_template('appointment.html')

@app.route('/disease')
def disease():
    return render_template('disease.html')

#------------

@app.route('/')
def home():
    return render_template('homepage.html')

@app.route('/predict', methods=['POST'])
def predict():
    symptoms = request.form.get("symptoms").strip()

    if not symptoms:
        return render_template('result.html', diseases=[])

    # Translate symptoms to English
    translation_prompt = f"Translate the following symptoms to English:\n\n{symptoms}"
    try:
        translation_response = model.generate_content(translation_prompt)
        translated_symptoms = translation_response.text.strip()
    except Exception as e:
        translated_symptoms = symptoms

    # Diagnosis prompt
    prompt = (
    "You are a professional doctor AI."
    " Analyze the symptoms given and return exactly 3 possible diagnoses in this strict format:"
    " Disease: [disease name]\\nConfidence: [percentage]%."
    " Example:\nDisease: Malaria\nConfidence: 80%\n\n"
    " Only output the formatted list, nothing else."
    f" Symptoms: {translated_symptoms}" 
    )


    try:
        response = model.generate_content(prompt)
        ai_text = response.text if response and response.text else "AI response not available."
    except Exception as e:
        ai_text = f"Please provide sufficient symptoms: {str(e)}"

    # Process results
    diseases = process_ai_response(ai_text)


    # --------------------------------------------------------
    # Get specialists list
    specialist_prompt = (
        "List the medical specialists who treat the following diseases."
        " Return only a Python list of strings, with no extra text or formatting."
        " The list should include exactly 3 specialist corresponding to disease."
        "\nDiseases:\n" + "\n".join([d['name'] for d in diseases])
    )

    specialist_response = model.generate_content(specialist_prompt)
    specialist_list = specialist_response.text.strip()
    #print("RAW SPECIALIST RESPONSE:\n", specialist_list)

   

    try:
        specialists = ast.literal_eval(specialist_list)
    except:
        specialists = []


    print("AI Response:", ai_text)  # Debugging output

    for s in specialists:
        print(s)
    
    while len(specialists) < len(diseases):
        specialists.append("General Physician")


    # return render_template('result.html', diseases=diseases)
    # return render_template('result.html', diseases=diseases, specialists=specialists)
    combined = list(zip(diseases, specialists))
    return render_template('result.html', combined=combined)



def process_ai_response(ai_text):
    # diseases = []
    # lines = ai_text.split("\n")

    # for i in range(len(lines)):
    #     if "Disease:" in lines[i]:
    #         name = lines[i].replace("Disease:", "").strip()
    #         if i + 1 < len(lines) and "Confidence:" in lines[i + 1]:
    #             confidence_str = re.search(r"(\d+)%", lines[i + 1])
    #             confidence = int(confidence_str.group(1)) if confidence_str else 0
    #             diseases.append({"name": name, "confidence": confidence})

    # return sorted(diseases, key=lambda x: x["confidence"], reverse=True)[:3]
    pattern = r"Disease:\s*(.*?)\s*Confidence:\s*(\d+)%"
    matches = re.findall(pattern, ai_text)

    diseases = [{"name": name.strip(), "confidence": int(confidence)} for name, confidence in matches]
    return sorted(diseases, key=lambda x: x["confidence"], reverse=True)[:3]




if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

