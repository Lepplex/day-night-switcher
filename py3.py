from pystray import Icon, MenuItem, Menu
from PIL import Image
import subprocess
import threading
import time
import os
import sys
from pathlib import Path
startup_message_status = 0

def disable_startup_message():
    global startup_message_status
    if startup_message_status == 0:
        startup_message_status = 1
        powershell_code = '''

        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
        $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText01)
        $text = $template.GetElementsByTagName("text")
        $text.Item(0).AppendChild($template.CreateTextNode("Startup notification disabled.")) > $null
        $toast = [Windows.UI.Notifications.ToastNotification]::new($template)
        $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Day/Night switcher")
        $notifier.Show($toast)

        '''
        subprocess.Popen(["powershell.exe", "-ExecutionPolicy", "Bypass", "-Command", powershell_code])
    else:
        startup_message_status = 0
        powershell_code = '''

        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
        $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText01)
        $text = $template.GetElementsByTagName("text")
        $text.Item(0).AppendChild($template.CreateTextNode("Startup notification enabled.")) > $null
        $toast = [Windows.UI.Notifications.ToastNotification]::new($template)
        $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Day/Night switcher")
        $notifier.Show($toast)

        '''
        subprocess.Popen(["powershell.exe", "-ExecutionPolicy", "Bypass", "-Command", powershell_code])



if startup_message_status == 0:
    powershell_code = '''

    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
    $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText01)
    $text = $template.GetElementsByTagName("text")
    $text.Item(0).AppendChild($template.CreateTextNode("D&N Switcher is running ! Take a look at the system tray.")) > $null
    $toast = [Windows.UI.Notifications.ToastNotification]::new($template)
    $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Day/Night switcher")
    $notifier.Show($toast)

    '''
    subprocess.Popen(["powershell.exe", "-ExecutionPolicy", "Bypass", "-Command", powershell_code])

def resource_path(relative_path):
    """Retourne le chemin absolu vers le fichier, fonctionnant dans un environnement compilé ou non."""
    try:
        base_path = Path(sys._MEIPASS)
    except AttributeError:
        base_path = Path(os.path.abspath("."))
    return base_path / relative_path

# Récupère l'état du thème (clair ou sombre)
def get_current_theme():
    ps_code = '''
    (Get-ItemPropertyValue -Path "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize" -Name SystemUsesLightTheme)
    '''
    result = subprocess.run(["powershell", "-Command", ps_code], capture_output=True, text=True)
    return "light" if result.stdout.strip() == "1" else "dark"

# Charge l'icône correspondant au thème actuel
def get_icon_image(theme):
    icon_path = resource_path(f"icon_{theme}.ico")
    if icon_path.exists():
        return Image.open(icon_path)
    else:
        return Image.new("RGB", (64, 64), "gray")  # Fallback

# Met à jour l'icône et le menu en fonction du thème actuel
def update_icon_and_menu(icon):
    current_theme = get_current_theme()
    icon.icon = get_icon_image(current_theme)
    # Met à jour le menu en fonction du thème courant
    if current_theme == "light":
        new_menu = Menu(
            MenuItem("Switch to dark mode", toggle_theme),
            MenuItem("Exit", quit_app)
        )
    else:
        new_menu = Menu(
            MenuItem("Switch to light mode", toggle_theme),
            MenuItem("Exit", quit_app)
        )
    icon.menu = new_menu

# Fonction de basculement du thème et mise à jour de l'icône/menu
def toggle_theme(icon, item):
    # Code PowerShell qui inverse le thème puis affiche une notification
    powershell_code = '''
    $key = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize"
    $current = Get-ItemPropertyValue -Path $key -Name SystemUsesLightTheme
    $new = if ($current -eq 1) { 0 } else { 1 }

    Set-ItemProperty -Path $key -Name AppsUseLightTheme -Value $new
    Set-ItemProperty -Path $key -Name SystemUsesLightTheme -Value $new

    Stop-Process -Name explorer -Force

    $message = if ($new -eq 1) { "Light mode enabled." } else { "Dark mode enabled." }

    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
    $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText01)
    $text = $template.GetElementsByTagName("text")
    $text.Item(0).AppendChild($template.CreateTextNode($message)) > $null
    $toast = [Windows.UI.Notifications.ToastNotification]::new($template)
    $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Day/Night switcher")
    $notifier.Show($toast)
    '''
    subprocess.Popen(["powershell.exe", "-ExecutionPolicy", "Bypass", "-Command", powershell_code])
    
    # Laisser un petit délai pour que Windows applique le changement
    time.sleep(2)
    # Mise à jour de l'icône et du menu
    update_icon_and_menu(icon)

# Quitter proprement l'application
def quit_app(icon, item):
    icon.stop()

# Création initiale de l'icône avec le menu qui dépend du thème courant
def create_icon():
    current_theme = get_current_theme()
    if current_theme == "light":
        menu = Menu(
            MenuItem("Switch to dark mode", toggle_theme),
            MenuItem("Disable/Enable startup notification...", disable_startup_message),
            MenuItem("Exit", quit_app)
        )
    else:
        menu = Menu(
            MenuItem("Switch to light mode", toggle_theme),
            MenuItem("Disable/Enable startup notification...", disable_startup_message),
            MenuItem("Exit", quit_app)
        )
    return Icon("ThemeSwitcher", icon=get_icon_image(current_theme), menu=menu)

# Point d'entrée de l'application
if __name__ == '__main__':
    icon = create_icon()
    # Utilisation d'un thread pour éviter de bloquer le script principal
    threading.Thread(target=icon.run).start()
