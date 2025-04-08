from pystray import Icon, MenuItem, Menu
from PIL import Image
import subprocess
import threading
import time
import os

# Charger l'icône en fonction du thème
def get_current_theme():
    ps_code = '''
    (Get-ItemPropertyValue -Path "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize" -Name SystemUsesLightTheme)
    '''
    result = subprocess.run(["powershell", "-Command", ps_code], capture_output=True, text=True)
    return "light" if result.stdout.strip() == "1" else "dark"

def get_icon_image(theme):
    filename = f"icon_{theme}.ico"
    if os.path.exists(filename):
        return Image.open(filename)
    else:
        return Image.new("RGB", (64, 64), "gray")  # Fallback

def update_icon(icon):
    theme = get_current_theme()
    icon.icon = get_icon_image(theme)

# Basculer le thème et mettre à jour l'icône
def toggle_theme(icon, item):
    powershell_code = '''
    $key = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize"
    $current = Get-ItemPropertyValue -Path $key -Name SystemUsesLightTheme
    $new = if ($current -eq 1) { 0 } else { 1 }

    Set-ItemProperty -Path $key -Name AppsUseLightTheme -Value $new
    Set-ItemProperty -Path $key -Name SystemUsesLightTheme -Value $new

    Stop-Process -Name explorer -Force

    $message = if ($new -eq 1) { "Thème clair activé." } else { "Thème sombre activé." }

    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
    $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText01)
    $text = $template.GetElementsByTagName("text")
    $text.Item(0).AppendChild($template.CreateTextNode($message)) > $null
    $toast = [Windows.UI.Notifications.ToastNotification]::new($template)
    $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Changer Thème")
    $notifier.Show($toast)
    '''
    subprocess.Popen(["powershell.exe", "-ExecutionPolicy", "Bypass", "-Command", powershell_code])
    
    # Attendre un peu le redémarrage, puis mettre à jour l’icône
    time.sleep(2)
    update_icon(icon)

# Quitter proprement
def quit_app(icon, item):
    icon.stop()

# Initialisation de l’icône
def create_icon():
    current_theme = get_current_theme()
    return Icon(
        "ThemeSwitcher",
        icon=get_icon_image(current_theme),
        menu=Menu(
            MenuItem("Changer thème", toggle_theme),
            MenuItem("Quitter", quit_app)
        )
    )

icon = create_icon()
threading.Thread(target=icon.run).start()
