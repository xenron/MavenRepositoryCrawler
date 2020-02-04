class RepositoryInfo:

    def __init__(self, groupId, artifact):
        self.groupId = groupId
        self.artifact = artifact
        self.version = None
        self.proceed = False


class ArtifactInfo:

    def __init__(self, groupId, artifact, url):
        self.groupId = groupId
        self.artifact = artifact
        self.url = url


if __name__ == '__main__':
    pass



