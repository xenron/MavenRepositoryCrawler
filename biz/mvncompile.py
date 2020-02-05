import os
import xml.etree.ElementTree as ET
from utils.log import getLogger


def rewrite_xml(item):
    logger = getLogger()
    logger.info("method [rewrite_xml] start")

    color_xml = "D:\Work\WangYue\\testmaven\pom.xml"
    updateTree = ET.parse(color_xml)
    XML_NS_NAME = ""
    XML_NS_VALUE = "http://maven.apache.org/POM/4.0.0"
    ET.register_namespace(XML_NS_NAME, XML_NS_VALUE)

    pre = "{http://maven.apache.org/POM/4.0.0}"
    root = updateTree.getroot()
    child_dep = root.find(pre + 'dependencies')
    dependency = child_dep.find(pre + 'dependency')
    for item in dependency:
        if item.tag == pre + 'groupId':
            item.text = item.groupId
        elif item.tag == pre + 'artifactId':
            item.text = item.artifact
        elif item.tag == pre + 'version':
            item.text = item.version

    updateTree.write(color_xml)
    logger.info("method [rewrite_xml] end")


def mvn_compile():
    logger = getLogger()
    logger.info("method [mvn_compile] start")

    os.chdir(r"D:\Work\WangYue\testmaven")
    a = os.system(r'D:\soft\Develop\apache-maven-3.5.0\bin\mvn compile 2>out.txt')

    logger.info("method [mvn_compile] end")
    return a
