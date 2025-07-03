import subprocess

def create_requirements_txt(path="requirements.txt"):
    """Erstellt eine requirements.txt-Datei mit UV"""
    try:
        result = subprocess.run(
            ["uv", "export", "--no-editable", "--no-hashes", "--no-dev"],
            capture_output=True, 
            text=True, 
            check=True
        )
        
        with open(path, "w") as f:
            f.write(result.stdout)
            
        print(f"requirements.txt erfolgreich erstellt unter: {path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Fehler beim Erstellen der requirements.txt: {e}")
        return False

# Beispielaufruf
if __name__ == "__main__":
    create_requirements_txt()
