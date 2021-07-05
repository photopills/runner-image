import os
import aiohttp
from gidgethub import aiohttp as gh_aiohttp
import pendulum


async def create_new_release(new_version: str, repo: str):
    if not new_version.startswith("v"):
        new_version = f"v{new_version}"

    token = os.getenv("GITHUB_TOKEN")
    async with aiohttp.ClientSession() as session:
        gh = gh_aiohttp.GitHubAPI(session, "fullonic", oauth_token=token)
        tag = await gh.post(
            f"https://api.github.com/repos/photopills/{repo}/releases",
            data={"tag_name": new_version, "name": f"{new_version} release"},
        )
        return tag


async def get_last_release_tag(repo) -> str:
    token = os.getenv("GITHUB_TOKEN")
    async with aiohttp.ClientSession() as session:
        gh = gh_aiohttp.GitHubAPI(session, "fullonic", oauth_token=token)
        tags = await gh.getitem(
            f"/repos/photopills/{repo}/releases",
        )
    release_index = 0
    last_release = pendulum.parse(tags.pop()["published_at"])
    for idx, tag in enumerate(tags):
        dt = pendulum.parse(tag["published_at"])
        if last_release < dt:
            last_release = dt
            release_index = idx
    print(tags[release_index]["tag_name"])
    return tags[release_index]["tag_name"]


async def create_pull_request(branch_name, repo, new_version, old_version):
    # https://docs.github.com/en/github-ae@latest/rest/reference/pulls#create-a-pull-request
    head = branch_name
    base = "master"
    token = os.getenv("GITHUB_TOKEN")
    async with aiohttp.ClientSession() as session:
        gh = gh_aiohttp.GitHubAPI(session, "fullonic", oauth_token=token)
        pull_url = (f"/repos/photopills/{repo}/pulls",)
        repo_url = f"https://github.com/photopills/{repo}"

        title = f"Bumps {repo} from {old_version} to {new_version}"
        body = f"Bumps [{repo}]({repo_url}) from {old_version} to {new_version}"
        info = await gh.post(
            pull_url, data={"head": head, "base": base, "title": title, "body": body}
        )
        return info
