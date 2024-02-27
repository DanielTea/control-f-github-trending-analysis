import subprocess
import os

def commit_and_push_to_github(github_token="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", repository_url="https://github.com/DanielTea/github-trending-analysis.git", csv_path='./trending_repositories_summary.csv'):
    # Configure your git settings
    os.environ['GIT_AUTHOR_NAME'] = 'Daniel Tremer'  # Change this to your name
    os.environ['GIT_AUTHOR_EMAIL'] = 'info@danieltremer.com'  # Change this to your email
    os.environ['GITHUB_TOKEN'] = github_token

    repository_url_with_token = repository_url.replace('https://', f'https://{github_token}@')


    tmp_dir = '/tmp/repo'
    if os.path.exists(tmp_dir):
        subprocess.run(['rm', '-rf', tmp_dir], check=True)
    subprocess.run(['git', 'clone', repository_url_with_token, tmp_dir], check=True)
    subprocess.run(['cp', csv_path, os.path.join(tmp_dir, 'trending_repositories_summary.csv')], check=True)
    os.chdir(tmp_dir)
    subprocess.run(['git', 'add', 'trending_repositories_summary.csv'], check=True)
    
    try:
        subprocess.run(['git', 'commit', '-m', 'Update trending repositories summary'], check=True)
        subprocess.run(['git', 'push', '--set-upstream', 'origin', 'main'], check=True, env={'GITHUB_TOKEN': github_token})
        print("Changes committed and pushed to repository.")
    except subprocess.CalledProcessError as e:
        if "nothing to commit" in e.stderr.decode('utf-8'):
            print("No changes to commit.")
        else:
            raise  # Re-raise the exception if it's due to another error
    
    # Cleanup: Change back to the original directory if needed and remove the tmp directory
    # os.chdir(original_directory)  # If you had an original directory to return to
    # subprocess.run(['rm', '-rf', tmp_dir], check=True)  # Clean up the temporary directory

# # Example usage
# github_token = 'your_github_token_here'
# repository_url = 'https://github.com/yourusername/yourrepository.git'
# csv_path = './trending_repositories_summary.csv'

# Call the function
commit_and_push_to_github()
