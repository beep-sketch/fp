from ultralytics import YOLO


model = YOLO('/models/weights/best.pt')
results = model.predict('inputs/video1.mp4', save= True)
print(results[0], '\n')
for box in results[0].boxes:
    print(box)