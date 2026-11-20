"""
VoiceMate Laptop Agent - Notification Helper Module.
Displays native Windows desktop notifications.
"""
import subprocess
import os

class NotificationHelper:
    @staticmethod
    def show_notification(title: str, message: str) -> str:
        """
        Displays a native Windows toast notification using PowerShell runtime.
        """
        clean_title = title.replace('"', '\"')
        clean_msg = message.replace('"', '\"')
        
        ps_cmd = f"""
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
        $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
        $textNodes = $template.GetElementsByTagName('text')
        $textNodes.Item(0).AppendChild($template.CreateTextNode("{clean_title}")) > $null
        $textNodes.Item(1).AppendChild($template.CreateTextNode("{clean_msg}")) > $null
        $toast = [Windows.UI.Notifications.ToastNotification]::new($template)
        [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("VoiceMate").Show($toast)
        """
        try:
            subprocess.Popen(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return "Notification shown."
        except Exception:
            try:
                from plyer import notification
                notification.notify(title=title, message=message, app_name="VoiceMate")
                return "Notification shown."
            except Exception:
                return "Failed to show notification."
