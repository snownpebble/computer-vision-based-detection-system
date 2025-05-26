# Computer Vision-Based Pothole Detection System

🚧 A YOLOv8-based system for detecting potholes in real-time using computer vision.

## 🔍 Features
- Real-time pothole detection using YOLOv8
- Streamlit-based interactive interface
- Road repair request system
- Onboarding tutorial & mascot
- Alert system for critical potholes

## 🛠️ Setup

1. Clone the repo:
  
   git clone https://github.com/snownpebble/computer-vision-based-detection-system.git
   cd computer-vision-based-detection-system

Create and activate a virtual environment:


python -m venv venv
source venv/bin/activate  # on Linux/macOS
venv\Scripts\activate     # on Windows
Install dependencies:


pip install -r requirements.txt
Run the app:


streamlit run app.py
📁 Project Structure

pothole-detection-app/
│
├── app.py
├── models/
├── utils/
├── data/
└── ...

📄 License
MIT License

yaml
Copy
Edit

---

### ✅ 2. **Create a `requirements.txt`**
Freeze your current environment’s packages:

```bash
pip freeze > requirements.txt
This ensures others can reproduce your environment exactly.

✅ 3. Optional: Add a .streamlit/config.toml
Customize Streamlit UI (like turning off the hamburger menu):
# .streamlit/config.toml
[theme]
primaryColor="#f63366"
backgroundColor="#ffffff"
secondaryBackgroundColor="#f0f2f6"
textColor="#262730"
font="sans serif"

[server]
runOnSave = true
✅ 4. Push the New Files

git add README.md requirements.txt .streamlit/config.toml
git commit -m "Add README, requirements, and Streamlit config"
git push
