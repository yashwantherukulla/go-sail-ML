import os
import json
import time
import logging
from collections import defaultdict
from groq import Groq
import instructor
import languages

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

class CodeAnalyser:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def get_code(self, file_path: str):
        with open(file_path, 'r') as f:
            code = f.read()
        return code

    def getOutput(self, filePath: str, sys_prompt, response_model):
        client = Groq(api_key=os.environ["GROQ_API_KEY"])
        client = instructor.from_groq(client, mode=instructor.Mode.TOOLS)

        output = client.chat.completions.create(
            model="llama-3.1-70b-versatile",#"mixtral-8x7b-32768",
            messages=[
                {
                    "role": "system",
                    "content": sys_prompt
                },
                {
                    "role": "user",
                    "content": self.get_code(filePath),
                }
            ],
            response_model=response_model,
        )
        return output

    def processRepos(self, root_folder):
        mapping = {}
        
        for repoName in os.listdir(root_folder):
            repoPath = os.path.join(root_folder, repoName)
            if os.path.isdir(repoPath):
                logging.info(f"Processing repo: {repoPath}")
                self.processRepo(repoPath, mapping)
                self.finalScores(repoPath)

        with open(os.path.join(repoPath, "file_output_mapping.json"), "w") as f:
            json.dump(mapping, f, indent=2)

    def processRepo(self, repoPath, mapping):
        outputFolder = os.path.join(repoPath, "output_data")
        os.makedirs(outputFolder, exist_ok=True)
        chunkFolderPath = os.path.join(repoPath, "chunk_data")
        for file in os.listdir(chunkFolderPath):
            filePath = os.path.join(chunkFolderPath, file)
            if os.path.isfile(filePath):
                logging.info(f"\tProcessing chunk: {filePath}")
                self.processChunk(filePath, outputFolder, mapping)
            time.sleep(0.75)

    def processChunk(self, filePath, outputFolder, mapping):
        try:
            output = self.getOutput(filePath).model_dump_json(indent=2)
            # get the filename without extension
            outputFilePath = os.path.join(outputFolder, f"{os.path.splitext(os.path.basename(filePath))[0]}.json")
            
            with open(outputFilePath, "w", encoding="utf-8") as f:
                f.write(output)
            
            mapping[filePath] = outputFilePath
        except Exception as e:
            self.logger.info(f"Error processing file {filePath}: {str(e)}")

    def finalScores(self, repoPath):
        directory = os.path.join(repoPath, "output_data")
        score_aggregation = defaultdict(int)
        files = 0

        for filename in os.listdir(directory):
            if filename.endswith('.json'):
                with open(os.path.join(directory, filename), 'r') as file:
                    data = json.load(file)

                for key, value in data.items():
                    if isinstance(value, dict) and 'score' in value:
                        score_aggregation[key] += value['score']
            files += 1

        for category in score_aggregation:
            score_aggregation[category] = round(score_aggregation[category]/files)

        output_data = {
            "scores_by_category": dict(score_aggregation)
        }

        output_file = os.path.join(repoPath, "output_data/scores_summary.json")
        with open(output_file, 'w') as file:
            json.dump(output_data, file, indent=2)

        self.logger.info(f"Scores summary saved to: {output_file}")

if __name__ == "__main__":
    base_path = "./cloned_repos"
    code_analyser = CodeAnalyser()
    code_analyser.processRepos(base_path)