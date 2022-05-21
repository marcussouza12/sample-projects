import time


def modifyCNPJ(string, method):
    if method == 'PARTIAL':
        string = insert_dash(string, 2, ".")
        string = insert_dash(string, 6, ".")

    elif method == 'COMPLETED':
        string = insert_dash(string, 2, ".")
        string = insert_dash(string, 6, ".")
        string = insert_dash(string, 10, "/")
        string = insert_dash(string, 15, "-")

    elif method == 'AUX':
        string = insert_dash(string, 3, ".")
        string = insert_dash(string, 7, ".")
        string = insert_dash(string, 11, "-")

    return string


def modifyCPF(string):
    string = insert_dash(string, 3, ".")
    string = insert_dash(string, 7, ".")
    string = insert_dash(string, 11, "-")

    return string


def modifyProcess(string, method):
    if method == 'PARTIAL':
        string = insert_dash(string, 7, "-")
        string = insert_dash(string, 10, ".")

    elif method == 'COMPLETED':
        string = insert_dash(string, 7, "-")
        string = insert_dash(string, 10, ".")
        string = insert_dash(string, 15, ".")
        string = insert_dash(string, 17, ".")
        string = insert_dash(string, 20, ".")

    elif method == 'AUX':
        string = insert_dash(string, 3, ".")
        string = insert_dash(string, 7, ".")
        string = insert_dash(string, 11, "-")

    return string


def insert_dash(string, index, value):
    return string[:index] + value + string[index:]


def removeField(map, field):
    if field in map.keys():
        del map[field]

    return map


def removeProcess(list, process):
    for obj in list:
        if obj["ref"] == process["ref"]:
            del obj

    return list


# method to get the downloaded file name
def getDownLoadedFileName(driver, waitTime):
    driver.execute_script("window.open()")
    # switch to new tab
    driver.switch_to.window(driver.window_handles[-1])
    # navigate to chrome downloads
    driver.get('chrome://downloads')
    # define the endTime
    endTime = time.time()+waitTime
    while True:
        try:
            # get downloaded percentage
            #downloadPercentage = driver.execute_script(
                #"return document.querySelector('downloads-manager').shadowRoot.querySelector('#downloadsList downloads-item').shadowRoot.querySelector('#progress').value")
            # check if downloadPercentage is 100 (otherwise the script will keep waiting)
            # if downloadPercentage == 100:
                # return the file name once the download is completed
            print("==========")
            return driver.execute_script("return document.querySelector('downloads-manager').shadowRoot.querySelector('#downloadsList downloads-item').shadowRoot.querySelector('div#content  #file-link').text")
        except:
            pass
        time.sleep(1)
        if time.time() > endTime:
            break
