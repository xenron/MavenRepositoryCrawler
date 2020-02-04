import math, os

if __name__ == '__main__':
    # keyword = "spring boot"
    #
    # keyword = keyword.replace(' ', '+')
    # print(keyword)

    # print(min(math.ceil(36/10), 5))
    # url = "https://mvnrepository.com/artifact/org.springframework/spring-jdbc"
    # split_list = url.split('/')
    # groupId = split_list[-2]
    # artifact = split_list[-1]
    # print(groupId)
    # print(artifact)
    # print(os.getcwd())
    # a = os.system(r"d:")
    # print(a)
    a = os.system("D:")
    # f = os.popen(r"cd D:\Work\WangYue\testmaven")
    os.chdir(r"D:\Work\WangYue\testmaven")
    print(os.getcwd())
    # a = os.system('pwd')
    # print(a)
    a = os.system(r'D:\soft\Develop\apache-maven-3.5.0\bin\mvn compile 2>out.txt')
    print(type(a))
    print(a)
