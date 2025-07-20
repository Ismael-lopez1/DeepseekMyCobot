import os
import sys
import re
import subprocess
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QComboBox, QLabel, QStackedWidget, QDialog, QPlainTextEdit, QHBoxLayout, QMessageBox)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from docx import Document
import openai
from openai import OpenAI as DeepSeekOpenAI

#Globals
recording = None
fs = 44100
recording_filename = "input.wav"
selected_language = "en"

# Whisper & DeepSeek API keys
openai.api_key = "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"
client = DeepSeekOpenAI(
    api_key="sk-1687a58d9aa04ebc878f20022bb60db6", base_url="https://api.deepseek.com")

generated_script_path = "C:\\Users\\iszi-\\Documents\\CS and CEng Projects\\DeepseekMyCobot\\generated_script.py"
docs_path= "C:\\Users\\iszi-\\Documents\\CS and CEng Projects\\DeepseekMyCobot\\Documentation"

# helpers
def extract_text_from_word(doc_path):
    """Extract from Word (.docx)"""
    doc = Document(doc_path)
    return "\n".join([para.text for para in doc.paragraphs])

def load_local_documents(directory):
    """Read all Word documents in a directory"""
    texts = []
    for filename in os.listdir(directory):
        if filename.endswith(".docx"):
            text = extract_text_from_word(os.path.join(directory, filename))
            texts.append(text)
    return texts

def record_audio(filename=recording_filename, duration=7):
    print(" Recording audio...")
    global recording
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()  # Wait until recording is finished
    wav.write(filename, fs, recording)

def execute_command(command):
    """Executes a shell command and returns stdout and stderr"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout, result.stderr
    except Exception as e:
        return None, str(e)
    
def run_command():
    """Runs the specific command and prints the output"""
    command = f"conda activate base && cd {os.path.dirname(generated_script_path)} && python {os.path.basename(generated_script_path)}"
    #print(f"\nRunning command: {command}")

    stdout, stderr = execute_command(command)

    if stdout:
        print(f"\nOutput:\n{stdout}")
    if stderr:
        print(f"\nError:\n{stderr}")

def confirm_and_run(code):
    dialog = QDialog()
    dialog.setWindowTitle("Edit and Confirm Script")
    layout = QVBoxLayout()

    text_edit = QPlainTextEdit()
    text_edit.setPlainText(code)    
    layout.addWidget(text_edit)

    run_button = QPushButton("Save and Run Script")
    run_button.clicked.connect(lambda: (save_code(text_edit.toPlainText()), dialog.accept()))
    layout.addWidget(run_button)

    dialog.setLayout(layout)
    dialog.exec_()

def save_code(code):
    with open(generated_script_path, "w", encoding="utf-8") as f:
        f.write(code)
    run_command()

# GUI Classes
class LanguageSelection(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Select Whisper Transcription Language:"))

        self.language_dropdown = QComboBox()
        self.language_dropdown.addItems(["en", "es"])
        layout.addWidget(self.language_dropdown)

        next_btn = QPushButton("Continue")
        next_btn.clicked.connect(self.go_next)
        layout.addWidget(next_btn)

        self.setLayout(layout)
    
    def go_next(self):
        global selected_language
        selected_language = self.language_dropdown.currentText()
        self.stacked_widget.setCurrentIndex(1)

class VoiceCommand(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.recording = False

        layout = QVBoxLayout()
        self.label = QLabel("Click microphone to start/stop recording")
        layout.addWidget(self.label)

        self.record_button = QPushButton("Start recording")
        self.record_button.clicked.connect(self.toggle_recording)
        layout.addWidget(self.record_button)

        self.submit_button = QPushButton("Submit to DeepSeek")
        self.submit_button.setEnabled(False)
        self.submit_button.clicked.connect(self.send_to_deepseek)
        layout.addWidget(self.submit_button)

        self.setLayout(layout)

    def toggle_recording(self):
        if not self.recording:
            self.label.setText("Recording...")
            self.record_button.setText("Stop recording")
            self.recording = True
            record_audio()
        else:
            self.recording = False
            self.label.setText("Recording finished")
            self.record_button.setText("Start recording")
            QMessageBox.information(self, "Info", "Recording finished")
            self.submit_button.setEnabled(True)

    def send_to_deepseek(self):
        word_documents = load_local_documents(docs_path)
        context = "\n".join(word_documents)

        with open(recording_filename, "rb") as audio_file:
            whisper_response = openai.audio.transcriptions.create(
                model="whisper-1", file=audio_file, language=selected_language
            )
        
        query = whisper_response.text
        completion = client.chat.completions.create(
            model="deepseek-chat",
            temperature=0.6,
            messages=[
                {"role": "system", "content": "You are mainly researching Python tasks for collaborative robotic arms using pymycobot."},
                {"role": "user", "content": f"reference text:\n{context}\n\n: {query} generate Python Script. Use COM7 serial port"}
            ]
        )

        message_content = completion.choices[0].message.content
        code_pattern = r"```python(.*?)```"
        matches = re.findall(code_pattern, message_content, re.DOTALL)
        python_code = "\n".join(matches).strip() if matches else message_content.strip()

        self.stacked_widget.widget(2).code = python_code
        self.stacked_widget.setCurrentIndex(2)

class CodeEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.code = ""
        self.setLayout(QVBoxLayout())
        self.text_edit = QPlainTextEdit()
        self.layout().addWidget(self.text_edit)

        run_button = QPushButton("Run Script")
        run_button.clicked.connect(self.run_script)
        self.layout().addWidget(run_button)

    def showEvent(self, event):
        self.text_edit.setPlainText(self.code)

    def run_script(self):
        confirm_and_run(self.text_edit.toPlainText())

app = QApplication(sys.argv)
stacks = QStackedWidget()
stacks.addWidget(LanguageSelection(stacks))
stacks.addWidget(VoiceCommand(stacks))
stacks.addWidget(CodeEditor())

window = QWidget()
window.setWindowTitle("Voice Command Python Generator")
layout = QVBoxLayout()
layout.addWidget(stacks)
window.setLayout(layout)
window.resize(600, 500)
window.show()
sys.exit(app.exec_())