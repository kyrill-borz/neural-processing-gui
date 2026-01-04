# neural-processing-gui
Neural Processing GUI

setup involves creating a venv:

```python
python -m venv .venv
.\.venv\Scripts\activate
pip install requirements.txt
git clone https://github.com/kyrill-borz/neural-processing-utils.git utils
```

To launch the gui, simply run 
```python
py .\main.py
```

This gui is made up of individual pages, which each have a folder, and then is run using main.py, window.py, and controller.py.

the global controller.py class allows all the data to be connected between pages 