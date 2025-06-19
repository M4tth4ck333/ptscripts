# Volume Shadow Copy Management (VSSManager)

A Python-based toolkit to manage Windows Volume Shadow Copies (VSS),
originally inspired by the VBS script from the "Lurking in the Shadows" 
talk by Mark Baggett and Tim Tomes.
Supports full CLI, GUI via Tkinter, modular usage, containerization with
Singularity, and Bash wrapping for integration into toolkits like ByKnocKulasT.
M4ttH4ck
---

## ✅ Features

* List, create, delete shadow copies
* Start/stop/query the VSS service
* CLI + GUI (Tkinter)
* Logging (to `vss.log`)
* Colored CLI output (`colorama`)
* Windows-compatible (requires `pywin32`)
* Works in Singularity (Windows containers)
* Importable as a Python module

---

## 🛠️ Installation

### Python Environment (Windows only)

```bash
pip install pywin32 colorama
```

### Files Required

```
.
├── vss.py
├── vss_gui.py (optional GUI)
├── vss_tests.py (optional tests)
├── singularity.def (optional container)
├── bash_wrapper.sh (optional wrapper)
```

---

## 🚀 CLI Usage

```bash
python vss.py --list
python vss.py --create C:
python vss.py --delete *
python vss.py --start
python vss.py --stop
python vss.py --status
```

---

## 🖥️ GUI Usage (optional)

```bash
python vss_gui.py
```

---

## 🧩 Module Usage (Python)

```python
from vss import VSSManager
vss = VSSManager()
vss.list_shadows()
vss.create_shadow("C:")
```

---

## 📦 Singularity (for Windows containers)

```bash
sudo singularity build vss.sif singularity.def
singularity run vss.sif --list
```

> ⚠️ Singularity with Windows containers requires a Windows host or VM.

---

## 🐚 Bash Wrapper (for WSL/Linux calling)

```bash
bash_wrapper.sh --list
```

---

## 📁 Logging

All activity is logged to `vss.log` with timestamps and log levels.

---

## 📌 Requirements

* Windows 10/11 or Server (32/64-bit)
* Python 3.6+
* Administrator privileges (for shadow copy actions)
* Modules: `pywin32`, `colorama`, `tkinter` (included with Python)

---

## 🔐 Use Case: Forensics, Incident Response, Red/Blue Teaming

Perfect for integration into forensic frameworks, IR pipelines, or adversary emulation platforms.

---

## 🧑‍💻 Authors

* Based on the VBS script by Mark Baggett & Tim "LaNMaSteR53" Tomes
* Python conversion, GUI and modular enhancements by the community

---

## 📜 License

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
