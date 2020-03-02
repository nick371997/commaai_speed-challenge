from keras.models import load_model
import pickle
import numpy as np
from postprocessor import PostProcessor
import pandas as pd
import training
import model

pre = PostProcessor()


def predictions(data, model):
    new_data = []
    for idx in range(1, len(data.index) - 1):
        row_now = data.iloc[[idx]].reset_index()
        row_prev = data.iloc[[idx - 1]].reset_index()
        row_next = data.iloc[[idx + 1]].reset_index()

        time_now = row_now[1].values[0]
        time_prev = row_prev[1].values[0]
        time_next = row_next[1].values[0]

        if time_now - time_prev > 0 and 0.0000001 < time_now - time_prev < 0.58:  # 0.578111 is highest diff i have seen
            row1 = row_prev
            row2 = row_now

        elif time_next - time_now > 0 and 0.0000001 < time_next - time_now < 0.58:
            row1 = row_now
            row2 = row_next

        x1, y1 = pre.preprocess_image_from_path(row1[0].values[0], row1[2].values[0])
        x2, y2 = pre.preprocess_image_from_path(row2[0].values[0], row2[2].values[0])

        img_diff = pre.optical_flow(x1, x2)
        img_diff = img_diff.reshape(1, img_diff.shape[0], img_diff.shape[1], img_diff.shape[2])
        y = np.mean([y1, y2])

        prediction = model.predict(img_diff)
        error = abs(prediction - y2)
        new_data.append([prediction[0][0], y2, error[0][0], time_now, time_prev])
    return pd.DataFrame(new_data)


def get_pred_mse(preds):
    df = pd.read_pickle(preds)
    avg = np.mean(df[2].values ** 2)
    return avg


if __name__ == "__main__":
    model = model.speed_model()
    model.load_weights("./model-weights.h5")

    df = pd.read_csv("./postprocessed.csv", header=None)
    print(df.shape)
    pre = PostProcessor()
    test = pre.shuffle_frame_pairs(df)
    print(test.shape)
    test_generator = training.generate_validation_data(test)
    val_score = model.evaluate_generator(test_generator, steps=len(test))
    data = predictions(test, model)
    print(data)
    data.to_csv('test96.csv', index=False)
    data.to_pickle("./postpredictions.pkl")

    print(get_pred_mse("postpredictions.pkl"))