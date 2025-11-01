from PyQt6.QtCore import QCoreApplication, QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest

app = QCoreApplication([])
manager = QNetworkAccessManager()

FileUrl = input("the url you want to download from:")
url = QUrl(FileUrl)
request = QNetworkRequest(url)

# download the file
reply = manager.get(request)

# print the contents of the file
with open("file.txt", 'w') as f:
    f.write(str(reply.readAll()))  # type: ignore