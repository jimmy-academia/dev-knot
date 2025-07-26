import os
import json

# Path to your result folder (change as needed)
RESULTS_FOLDERs = ["results/got4_4/got4", "results/got4_2/got4", "results/got4_1/got4"]

def evaluate_accuracy(results_folders):
    for results_folder in results_folders:
        files = [f for f in os.listdir(results_folder) if f.endswith(".json")]
        total = len(files)
        correct = 0

        for file in files:
            with open(os.path.join(results_folder, file), "r") as f:
                graph = json.load(f)
                solved = False
                if 'problem_solved' in graph[-2]:
                    solved = graph[-2]["problem_solved"][0]  # second-to-last record
                if solved:
                    correct += 1
                # print(f"{file}: {'Correct' if solved else 'Incorrect'}")

        accuracy = correct / total if total > 0 else 0
        print(results_folder)
        print(f"\nOverall accuracy: {correct}/{total} = {accuracy:.2%}")

if __name__ == "__main__":
    evaluate_accuracy(RESULTS_FOLDERs)
