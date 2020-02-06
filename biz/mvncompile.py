import os
import xml.etree.ElementTree as ET
from utils.log import getLogger
from utils.common import ConfigUtil

# 读取配置文件
config = ConfigUtil()

def rewrite_xml(item):
    logger = getLogger()
    logger.info("method [rewrite_xml] start")

    pwd = os.getcwd()
    pom_path = os.path.join(pwd, "data", "pom.xml")
    updateTree = ET.parse(pom_path)
    XML_NS_NAME = ""
    XML_NS_VALUE = "http://maven.apache.org/POM/4.0.0"
    ET.register_namespace(XML_NS_NAME, XML_NS_VALUE)

    pre = "{http://maven.apache.org/POM/4.0.0}"
    root = updateTree.getroot()
    child_dep = root.find(pre + 'dependencies')
    dependency = child_dep.find(pre + 'dependency')
    for de in dependency:
        if de.tag == pre + 'groupId':
            de.text = item.groupId
        elif de.tag == pre + 'artifactId':
            de.text = item.artifact
        elif de.tag == pre + 'version':
            de.text = item.version

    updateTree.write(pom_path)
    logger.info("method [rewrite_xml] end")


def mvn_compile():
    logger = getLogger()
    logger.info("method [mvn_compile] start")
    mvn_path = config.load_value('system', 'mvn_path', '')

    pwd = os.getcwd()
    pom_path = os.path.join(pwd, "data", "pom.xml")
    log_path = os.path.join(pwd, "logs", "error.txt")
    command = "{0} -f {1} compile 2>{2}".format(mvn_path, pom_path, log_path)
    a = os.system(command)

    logger.info("method [mvn_compile] end")
    return a


if __name__ == '__main__':
    mvn_compile()