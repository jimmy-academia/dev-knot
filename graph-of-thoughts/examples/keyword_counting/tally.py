import os
import json

# Path to your result folder (change as needed)
RESULTS_FOLDER = "examples/keyword_counting/results/<your-folder-name>/got4"

def evaluate_accuracy(results_folder):
    files = [f for f in os.listdir(results_folder) if f.endswith(".json")]
    total = len(files)
    correct = 0

    for file in files:
        with open(os.path.join(results_folder, file), "r") as f:
            graph = json.load(f)
            solved = graph[-2]["problem_solved"][0]  # second-to-last record
            if solved:
                correct += 1
            print(f"{file}: {'Correct' if solved else 'Incorrect'}")

    accuracy = correct / total if total > 0 else 0
    print(f"\nOverall accuracy: {correct}/{total} = {accuracy:.2%}")

if __name__ == "__main__":
    evaluate_accuracy(RESULTS_FOLDER)
