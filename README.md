# h07x | Web Cloner 🌐

A Website Cloning Tool by h07x

h07x Web Cloner is a Python-based tool designed to clone website frontends and available assets, preview cloned pages locally, and access generated source files.

# ✨ FEATURES

- 🌐 Website frontend cloning
- 🎨 Asset retrieval
- 👁️ Local website preview
- 📦 Generated source files
- ⚡ Simple command-line interface

📱 INSTALLATION — TERMUX

1. Install Termux

Download Termux from a trusted source:

- "F-Droid" (https://f-droid.org/packages/com.termux/)
- "GitHub" (https://github.com/termux/termux-app)

2. Update Termux

pkg update && pkg upgrade -y

3. Install dependencies

pkg install git python -y

4. Clone the repository

cd ~
git clone https://github.com/h07x/h07x-Web-Copy.git

5. Enter the project directory

cd ~/h07x-Web-Copy

6. Install Python requirements

If a "requirements.txt" file exists:

python -m pip install -r requirements.txt

7. Find the main script

find . -type f -name "*.py"

If the main script is named "h07x | Web Copy.py" in the current directory, execute:

python "h07x | Web Copy.py"

Use the actual filename returned by "find" if it differs.

🚀 QUICK START

After the first installation, start the tool with:

cd ~/h07x-Web-Copy
python "h07x | Web Copy.py"

Enter the target website URL when prompted.

🔄 UPDATE THE TOOL

cd ~/h07x-Web-Copy
git pull

🛠️ TROUBLESHOOTING

Repository already exists

cd ~/h07x-Web-Copy

Python is missing

pkg install python -y

Git is missing

pkg install git -y

Find Python files

find ~/h07x-Web-Copy -type f -name "*.py"

⚠️ DISCLAIMER

Use this tool only on websites you own or have permission to reproduce. Respect intellectual property, privacy, and applicable laws. This tool does not automatically copy private server-side code, databases, or backend functionality.

👨‍💻 DEVELOPER

h07x

Repository: "H07X-Web-Copy" (https://github.com/h07x/h07x-Web-Copy)

Built for developers, learners, and frontend experimentation.