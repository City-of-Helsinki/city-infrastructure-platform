import os


def git_version(request):
    """
    Gets VERSION env variable and sets it to the context.
    VERSION is set in the deployment pipelines
    """
    return {"GIT_VERSION": os.environ.get("VERSION", "not found")}
