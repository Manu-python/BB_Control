import time


class AppLogger:
    """
    Central logging utility.
    Formats log messages into styled HTML.
    """

    @staticmethod
    def format(message: str, message_type: str = "info") -> str:
        timestamp = time.strftime("[%H:%M:%S]")

        if message_type == "success":
            color = "#7FFF00"
        elif message_type == "error":
            color = "#FF4500"
        elif message_type == "warning":
            color = "#FFFF00"
        elif message_type.startswith("RX"):
            color = "#4CAF50"
        elif message_type.startswith("TX"):
            color = "#9932CC"
        else:
            color = "#E0E0E0"

        return (
            f'<span style="color: #FFFFFF;"><b>{timestamp}</b></span> '
            f'<span style="color: {color};">{message}</span>'
        )
