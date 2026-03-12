import cv2
import mediapipe as mp
import math

mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_draw = mp.solutions.drawing_utils


def calculate_angle(a, b, c):
    a = [a.x, a.y]
    b = [b.x, b.y]
    c = [c.x, c.y]

    angle = math.degrees(
        math.atan2(c[1] - b[1], c[0] - b[0]) -
        math.atan2(a[1] - b[1], a[0] - b[0])
    )

    angle = abs(angle)
    if angle > 180:
        angle = 360 - angle

    return angle


def analyze_posture(exercise_type):
    cap = cv2.VideoCapture(0)

    feedback = "No posture detected"

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = pose.process(image)

        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        if result.pose_landmarks:
            lm = result.pose_landmarks.landmark

            if exercise_type == "squat":
                hip = lm[mp_pose.PoseLandmark.LEFT_HIP.value]
                knee = lm[mp_pose.PoseLandmark.LEFT_KNEE.value]
                ankle = lm[mp_pose.PoseLandmark.LEFT_ANKLE.value]

                angle = calculate_angle(hip, knee, ankle)

                if angle < 100:
                    feedback = "Good squat depth 👍"
                else:
                    feedback = "Go lower ⚠️ Bend knees more"

            elif exercise_type == "pushup":
                shoulder = lm[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
                elbow = lm[mp_pose.PoseLandmark.LEFT_ELBOW.value]
                wrist = lm[mp_pose.PoseLandmark.LEFT_WRIST.value]

                angle = calculate_angle(shoulder, elbow, wrist)

                if angle > 160:
                    feedback = "Lower your body ⚠️"
                else:
                    feedback = "Good push-up form 👍"

            elif exercise_type == "plank":
                shoulder = lm[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
                hip = lm[mp_pose.PoseLandmark.LEFT_HIP.value]
                ankle = lm[mp_pose.PoseLandmark.LEFT_ANKLE.value]

                angle = calculate_angle(shoulder, hip, ankle)

                if 160 < angle < 180:
                    feedback = "Great plank 🔥"
                else:
                    feedback = "Keep body straight ⚠️"

            mp_draw.draw_landmarks(image, result.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        cv2.imshow("Form Check", image)

        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    return feedback
