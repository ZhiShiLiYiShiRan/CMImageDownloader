# uploader/record.py

from flask import Blueprint, render_template

record_bp = Blueprint("record", __name__)

@record_bp.route("/record_test")
def record_test():
    test_data = {
        "_id": "123456",
        "Label": "B",
        "Number": "25001",
        "Note": "原包装有轻微压痕，功能完好",
        "Image_count": 3,
        "QA": "Jasper",
        "QA_time": "2025-07-08 14:00",
        "Product_image": [
            "https://via.placeholder.com/150",
            "https://via.placeholder.com/150",
            "https://via.placeholder.com/150"
        ]
    }
    return render_template("record.html", item=test_data)
