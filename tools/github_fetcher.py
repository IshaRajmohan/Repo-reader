import requests
import base64
from google import genai
from dotenv import load_dotenv
import os
import json
load_dotenv()

client=genai.Client(api_key="GEMINI_API_KEY")
#returns the owner and repo name(tuple)
def parse_github_url(url):
    l=url.split("/")
    t=(l[3],l[4])#(owner,repo)
    return t
#returns list of all the paths in the repo
def get_file_tree(owner,repo):
    url=f"https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1"
    response=requests.get(url)
    data=response.json()
    file_paths=[]
    for item in data['tree']:
        if item['type']=="blob":
            file_paths.append(item['path'])
    return file_paths

#returns the content of the file , given the path
def get_file_content(owner, repo, path):
    url=f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    response=requests.get(url)
    data=response.json()
    content = base64.b64decode(data["content"]).decode("utf-8")
    return content

#given url-> using parse_github_url fetches owner and repo-> 
#gets file paths using get_file_tree-> gets depencency files+content-> 
#gets entry point files+content-> gets readme content
#final output -dictionary with file paths, readme, dependency files+content, entry point files+content

def fetch_repo(url):
    owner,repo=parse_github_url(url)
    file_paths=get_file_tree(owner, repo)
    dependency_files=['requirements.txt','package.json','pyproject.toml','Cargo.toml','go.mod']
    dependency_content={}
    #entry_files=['main.py', 'app.py', 'index.js', 'index.ts', 'main.go',' main.rs']
    entry_content={}
    final={}
    for item in file_paths:
        file_name=item.split("/")[-1]
        if file_name in dependency_files:
            dependency_content[item]=get_file_content(owner,repo,item)
        if file_name.lower() == "readme.md":
            final["readme"]=get_file_content(owner,repo,item)

    
    prompt = f"""Given this file tree from a code repository, identify the entry point file(s) - 
                the files where execution begins (e.g. a Flask app's run.py, a Next.js app's main pages).

                File tree:
                {file_paths}

                Respond with ONLY a JSON array of file paths, nothing else. Example: ["backend/run.py", "frontend/src/app/page.tsx"]
                """
    response=client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )


    text = response.text.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    entry_paths = json.loads(text)
    final["file_tree"]=file_paths
    final["dependency_files"]=dependency_content
    for i in entry_paths:
        entry_content[i]=get_file_content(owner,repo, i)
    final["entry_point_files"]=entry_content
    
    

    return final


if __name__ == "__main__":
    
    data = fetch_repo("https://github.com/IshaRajmohan/MoodBeats")
    
    print(json.dumps(data, indent=2))

            
        

