from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriver
from models import Course
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import random as r

# import json

# initailaize variables used in the scrapping
ignored_exceptions = (
    NoSuchElementException,
    StaleElementReferenceException,
)
driver = webdriver.Chrome()
wait = WebDriverWait(driver, 50, ignored_exceptions=ignored_exceptions)
hotfix_flip = True
first = True
course_info = {}
r.seed(12334)


def find(driver):
    element = driver.find_element(
        By.XPATH,
        "/html/body/div/form[1]/div/div/div[2]/div[1]/div/div/div/div/div/div[3]/div/div[2]/div/div[4]/div[2]/div/div/div/div/input",
    )
    if element:
        return element
    else:
        return False


def qu_login():
    driver.get(
        "https://saself.ps.queensu.ca/psc/saself/EMPLOYEE/SA/c/SA_LEARNER_SERVICES.CLASS_SEARCH.GBL?Page=SSR_CLSRCH_ENTRY&Action=U"
    )
    # put in email
    element = wait.until(EC.visibility_of_element_located((By.ID, "i0116")))
    element.send_keys("QUEENS@EMAIL")
    element = driver.find_element_by_id("idSIButton9")
    element.click()

    # put in password
    element = driver.find_element_by_id("i0118")
    element.send_keys("QUEENS_PASSWORD")
    element = wait.until(find)
    element.click()

    # 2FA: do the two factor authenication step manually


def get_subjects(semester):
    driver.implicitly_wait(15)
    semester_string = "{} {}".format(semester["year"], semester["term"])
    driver.get(
        "https://saself.ps.queensu.ca/psc/saself/EMPLOYEE/SA/c/SA_LEARNER_SERVICES.CLASS_SEARCH.GBL?Page=SSR_CLSRCH_ENTRY&Action=U"
    )
    # Semester Selection
    element = wait.until(
        EC.presence_of_element_located((By.ID, "CLASS_SRCH_WRK2_STRM$35$"))
    )
    for option in element.find_elements_by_tag_name("option"):
        if option.text == semester_string:
            option.click()
            break

    # Wait for semester to be fetched
    wait.until(EC.invisibility_of_element_located((By.ID, "WAIT_win0")))
    element = driver.find_element_by_id("SSR_CLSRCH_WRK_SUBJECT_SRCH$0")
    return element.find_elements_by_tag_name("option")


def get_courses(semester, subject_idx):
    global hotfix_flip
    global course_info

    semester_string = "{} {}".format(semester["year"], semester["term"])
    driver.get(
        "https://saself.ps.queensu.ca/psc/saself/EMPLOYEE/SA/c/SA_LEARNER_SERVICES.CLASS_SEARCH.GBL?Page=SSR_CLSRCH_ENTRY&Action=U"
    )
    # Semester Selection
    element = wait.until(
        EC.presence_of_element_located((By.ID, "CLASS_SRCH_WRK2_STRM$35$"))
    )
    for option in element.find_elements_by_tag_name("option"):
        if option.text == semester_string:
            option.click()
            break

    # Wait for semester to be fetched and pick subject
    wait.until(EC.invisibility_of_element_located((By.ID, "WAIT_win0")))
    element = driver.find_element_by_id("SSR_CLSRCH_WRK_SUBJECT_SRCH$0")
    option = element.find_elements_by_tag_name("option")[subject_idx]
    option.click()

    hotfix = option.text == "Applied Science"
    if hotfix:
        # Less than OR greater than
        element = driver.find_element_by_id("SSR_CLSRCH_WRK_SSR_EXACT_MATCH1$1")
        element.send_keys("l" if hotfix_flip else "g")
        hotfix_flip = not hotfix_flip
        # Boundry point
        element = driver.find_element_by_id("SSR_CLSRCH_WRK_CATALOG_NBR$1")
        element.send_keys("150")
    else:
        # Contains ""
        element = driver.find_element_by_id("SSR_CLSRCH_WRK_SSR_EXACT_MATCH1$1")
        element.send_keys("c")

    # Undergrad only
    element = driver.find_element_by_id("SSR_CLSRCH_WRK_ACAD_CAREER$2")
    option = element.find_elements_by_tag_name("option")[0]
    option.click()
    # Main campus only
    element = driver.find_element_by_id("SSR_CLSRCH_WRK_CAMPUS$3")
    element.send_keys("m")
    # Show non open classes
    element = driver.find_element_by_id("SSR_CLSRCH_WRK_SSR_OPEN_ONLY$5")
    if element.is_selected():
        element.click()

    # Click search
    element = driver.find_element_by_id("CLASS_SRCH_WRK2_SSR_PB_CLASS_SRCH")
    element.click()

    # See if search gets results
    try:
        wait.until(
            lambda driver: driver.find_elements(
                By.ID, "CLASS_SRCH_WRK2_SSR_PB_MODIFY$5$"
            )
            or driver.find_elements(
                By.XPATH,
                "//*[contains(text(), 'The search returns no results that match the criteria specified.')]",
            )
        )
    except:
        return "Error with search"

    courses = driver.find_elements_by_xpath(
        "//div[starts-with(@id,'win0divSSR_CLSRSLT_WRK_GROUPBOX2$')]"
    )

    # iterate through all courses on the page
    for course_div in courses:
        # get and format the course code of each course
        course_desc = course_div.find_element_by_tag_name("a").get_attribute("title")
        course_code = course_desc[17 : course_desc.index(" -")].replace(" ", "")
        course_code = (
            course_code[:-1]
            if course_code[-1] == "A" or course_code[-1] == "B"
            else course_code
        )
        for i in range(len(course_code) - 1):
            if not course_code[i].isdigit() and course_code[i + 1].isdigit():
                course_code = course_code[: i + 1] + "-" + course_code[i + 1 :]
                break

        course_name = course_desc[course_desc.index(" -") + 2 :].strip()

        # find professor name(s) of the course
        profnames = course_div.find_elements_by_xpath(
            ".//div[starts-with(@id,'win0divMTG_INSTR$')]"
        )
        proflis = []
        first = True
        # iterate through all retreived professor names
        for profname in profnames:
            # only take the first name(s) for the course section
            if first:
                prof = profname.text

                if "\n" in prof:
                    proflis = prof.split("\n")
                else:
                    proflis.append(prof)

                proflis = [*set(proflis)]
                first = False

        # if the prof name is staff then it doesn't need any further formatting
        if "Staff" not in proflis:
            prof_lis_format = []
            # if there are multiple professors for one course go through and format all of them
            if len(proflis) > 1:
                for prof in proflis:
                    prof_cut = prof[: len(prof) - 1]
                    # replace the ',' inbetween first and last names with a ' ' and adding a ',' to separate each professor
                    if "," in prof_cut:
                        prof_chg = (
                            prof_cut[prof_cut.index(",") + 1 :]
                            + " "
                            + prof_cut[: prof_cut.index(",")]
                        )
                        if prof_chg == " ":
                            prof_chg = "Staff"
                    # if there is no ',' in the name then no formatting in needed
                    else:
                        if prof == " ":
                            prof_chg = "Staff"
                        else:
                            prof_chg = prof
                    prof_lis_format.append(prof_chg)

            else:
                # replace the ',' inbetween first and last names with a ' ' and adding a ',' to separate each professor
                if "," in proflis[0]:
                    prof_chg = (
                        proflis[0][proflis[0].index(",") + 1 :]
                        + " "
                        + proflis[0][: proflis[0].index(",")]
                    )
                    if prof_chg == " ":
                        prof_chg = "Staff"

                # if there is no ',' in the name then no formatting in needed
                else:
                    if proflis[0] == " ":
                        prof_chg = "Staff"
                    else:
                        prof_chg = proflis[0]
                prof_lis_format.append(prof_chg)
        proflis = ",".join(prof_lis_format)

        # add gathered data to the global dictionary holding all class data
        course_info[course_code] = {
            "prof_name": proflis,
            "course_name": course_name,
            "course_code": course_code,
        }


def get_gpa(course_code):
    # go to coursecentral website for the given course using the course code
    driver.get("https://coursecentral.ca/schools/queens/{}".format(course_code))
    try:
        # try and find if there is no results for the course
        element = driver.find_element_by_xpath("//h1[contains(text(), '404')]")
    except:
        element = None

    if not element:
        # if there are results for the course then find the element with the
        # course description, average gpa, and average enrollment
        element = driver.find_element_by_xpath("//div[contains(text(), 'Description')]")
        # find the average enrollment and gpa for the course
        avg_gpa_enroll = element.find_element_by_xpath(
            "//p[starts-with(@class, 'css-')]"
        ).text
        # find the average gpa of the course by formatting the the string with both
        # gpa and enrollment
        avg_gpa = avg_gpa_enroll[
            avg_gpa_enroll.index("Average GPA: ") + 13 : avg_gpa_enroll.index("\n")
        ]
        # find the average enrollment of the course by formatting the string with both
        # gpa and enrollment
        avg_enroll = avg_gpa_enroll[avg_gpa_enroll.index("Average Enrollment: ") + 20 :]

        # find the description for the course by formatting the string with both gpa
        # and enrollment
        desc = element.find_element_by_xpath(".//p[starts-with(@class, 'css-')]").text

        # add all found data to the global dictionary holding all gathered class data
        course_dict = course_info[course_code]
        course_dict["course_desc"] = desc
        course_dict["avg_enroll"] = avg_enroll
        course_dict["avg_gpa"] = avg_gpa
        course_dict["gpa_url"] = driver.current_url
        course_info[course_code] = course_dict
    else:
        # if the course is not found then there will be no information to gather
        # set all potential fields to "N/A" and add it to the golbal dictionary
        # holding all class data
        course_dict = course_info[course_code]
        course_dict["course_desc"] = "N/A"
        course_dict["avg_enroll"] = "N/A"
        course_dict["avg_gpa"] = "N/A"
        course_dict["gpa_url"] = "N/A"
        course_info[course_code] = course_dict


def get_rmp(course_code, done_profs):
    # scrape rate my prof info
    global first

    # get the list of gathered professor name(s) for the current course code
    prof_name = course_info[course_code]["prof_name"]

    # precautionary try block so if one element is not found, the whole
    # program doesn't blow up with all the gathered data
    try:
        # if there are multiple professor names for the course, find all data
        # for each professor
        if "," in prof_name:
            # initialize variables used to store respecitve data we are trying to find
            # and split up the string of professor names into a list
            proflis = prof_name.split(",")
            profScores = []
            profUrls = []

            # iterate through all professor names
            for prof in proflis:
                # if information for the professor is not already found, gather it
                if prof not in done_profs:
                    # go to rate my prof
                    driver.get("https://www.ratemyprofessors.com/school?sid=1466")

                    # block of code used to initally set the school and get rid of the
                    # pop up shown on first load of the website
                    if first:
                        element = driver.find_element_by_xpath(
                            "//button[contains(text(), 'Close')]"
                        ).click()
                        element = driver.find_element_by_xpath(
                            "//input[starts-with(@placeholder, 'Your school')]"
                        )
                        element.send_keys("queen's")
                        element = wait.until(
                            EC.presence_of_element_located(
                                (
                                    By.XPATH,
                                    "//a[starts-with(@href, '/school?sid=1466')]",
                                )
                            )
                        )
                        element.click()
                        first = False

                    # go to the queen's school page of rate my prof
                    driver.get("https://www.ratemyprofessors.com/school?sid=1466")

                    # identify the search bar and search for the professor
                    element = wait.until(
                        EC.presence_of_element_located(
                            (
                                By.XPATH,
                                "//input[starts-with(@placeholder, 'Professor name')]",
                            )
                        )
                    )
                    element.send_keys(prof)
                    element.send_keys(Keys.ENTER)
                    element.send_keys(Keys.TAB)

                    try:
                        # try and find if the professor is not in their system
                        element = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located(
                                (
                                    By.XPATH,
                                    "//div[contains(text(), 'No professors with')]",
                                )
                            )
                        )
                    except:
                        # professor is in their system
                        element = None

                    if not element:
                        # if the profess is in their system then get their rating and url to their
                        # rate my prof page
                        rmp = wait.until(
                            EC.presence_of_element_located(
                                (
                                    By.XPATH,
                                    "//div[starts-with(@class, 'CardNumRating__CardNumRatingNumber-sc-')]",
                                )
                            )
                        ).text
                        url = driver.find_element_by_xpath(
                            "//a[starts-with(@class, 'TeacherCard__StyledTeacherCard-')]"
                        ).get_attribute("href")

                        # add gathered data for the prof to the lists used to temporarily store the information
                        profScores.append(rmp)
                        profUrls.append(url)

                        # add the professor's information to the dictionary of found professors so this process
                        # does not need to be repeated
                        done_profs[prof] = [
                            rmp,
                            url,
                        ]
                    else:
                        # if the professor page is not found on rate my prof then set
                        # the rate my prof score and rate my prof url to "N/A"
                        rmp = "N/A"
                        profScores.append(rmp)
                        profUrls.append("N/A")

                        # Add professor info to dictionary of found professors so this process does not need
                        # to be repeated
                        done_profs[prof] = [rmp, "N/A"]
                else:
                    # if the professor's info has already been found previously, find it, then add it
                    # to the temporary lists for the information
                    profScores.append(done_profs[prof][0])
                    profUrls.append(done_profs[prof][1])

            # once all professors in the list have been queried, add the information to the
            # global dictionary containing all class information
            course_dict = course_info[course_code]
            course_dict["rmp"] = ",".join(profScores)
            course_dict["prof_url"] = ",".join(profUrls)
            course_info[course_code] = course_dict

        else:
            # if there is only one name for the coressponding class, do the following:
            if prof_name not in done_profs:
                # go to rate my prof
                driver.get("https://www.ratemyprofessors.com/school?sid=1466")

                # block of code used to initally set the school and get rid of the
                # pop up shown on first load of the website
                if first:
                    element = driver.find_element_by_xpath(
                        "//button[contains(text(), 'Close')]"
                    ).click()
                    element = driver.find_element_by_xpath(
                        "//input[starts-with(@placeholder, 'Your school')]"
                    )
                    element.send_keys("queen's")
                    element = wait.until(
                        EC.presence_of_element_located(
                            (By.XPATH, "//a[starts-with(@href, '/school?sid=1466')]")
                        )
                    )
                    element.click()
                    first = False

                # identify the search bar and search for the professor
                element = wait.until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH,
                            "//input[starts-with(@placeholder, 'Professor name')]",
                        )
                    )
                )
                element.send_keys(prof_name)
                element.send_keys(Keys.ENTER)
                element.send_keys(Keys.TAB)

                try:
                    # try and find if the professor is not in their system
                    element = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located(
                            (By.XPATH, "//div[contains(text(), 'No professors with')]")
                        )
                    )
                except:
                    # professor is in their system
                    element = None

                if not element:
                    # if the profess is in their system then get their rating and url to their
                    # rate my prof page
                    rmp = wait.until(
                        EC.presence_of_element_located(
                            (
                                By.XPATH,
                                "//div[starts-with(@class, 'CardNumRating__CardNumRatingNumber-sc-')]",
                            )
                        )
                    ).text

                    url = driver.find_element_by_xpath(
                        "//a[starts-with(@class, 'TeacherCard__StyledTeacherCard-')]"
                    ).get_attribute("href")

                    # once all professor data has been queried, add the information to the
                    # global dictionary containing all class information
                    course_dict = course_info[course_code]
                    course_dict["rmp"] = rmp
                    course_dict["prof_url"] = url
                    course_info[course_code] = course_dict
                    done_profs[prof_name] = [rmp, url]
                else:
                    # if the professor page is not found on rate my prof then set
                    # the rate my prof score and rate my prof url to "N/A"
                    rmp = "N/A"
                    course_dict = course_info[course_code]
                    course_dict["rmp"] = rmp
                    course_dict["prof_url"] = "N/A"
                    course_info[course_code] = course_dict

                    # Add professor info to dictionary of found professors so this process does not need
                    # to be repeated
                    done_profs[prof_name] = [rmp, url]
            else:

                # if the professor's info has already been found previously, find it, then add it
                # to the temporary lists for the information
                course_dict = course_info[course_code]
                course_dict["rmp"] = done_profs[prof_name][0]
                course_dict["prof_url"] = done_profs[prof_name][1]
                course_info[course_code] = course_dict
            return "Success"
    except:
        return "Done"


# with open(r"C:\Users\matth\Desktop\course_find_api\scrapers\courses.json") as json_file:
#     course_info = json.load(json_file)

semester = {"year": "2023", "term": "Winter"}

qu_login()

# get data from QueensU for course codes and professor names
subjets = get_subjects(semester)
subject_names = [subject.text for subject in subjets]
for idx, subject_name in enumerate(subject_names):
    if subject_name == " ":
        continue

    status = get_courses(semester, idx)

    print("{} - {} - {}".format(str(idx).zfill(3), subject_name.ljust(30), status))

# print(course_info)

# get the gpas, and average enrollment for all queried courses
for key, value in course_info.items():
    get_gpa(key)
    print(
        "{} - average gpa: {} - average enrollment: {} URL: {}".format(
            str(key).zfill(3),
            course_info[key]["avg_gpa"].ljust(30),
            course_info[key]["avg_enroll"],
            course_info[key]["gpa_url"],
        )
    )

# print(course_info)

# get the rate my profs for all professors found for each class queried
first = True
done_profs = {}
for key, value in course_info.items():
    if "Staff" not in course_info[key]["prof_name"]:
        status = get_rmp(key, done_profs)
        print(
            "{} - {} - rate my prof: {} URL: {} {}".format(
                str(key).zfill(3),
                course_info[key]["prof_name"].ljust(30),
                course_info[key]["rmp"],
                course_info[key]["prof_url"],
                status,
            )
        )
    else:
        course_info[key]["rmp"] = "N/A"
        course_info[key]["prof_url"] = "N/A"
        print(
            "{} - {} - rate my prof: {} URL:{} {}".format(
                str(key).zfill(3),
                course_info[key]["prof_name"].ljust(30),
                course_info[key]["rmp"],
                course_info[key]["prof_url"],
                "Success",
            )
        )

# print(course_info)

# Add all queried information to a database for storage
for key, value in course_info.items():
    engine = create_engine("sqlite:///courseFind.db")
    Session = sessionmaker(bind=engine)
    session = Session()

    new_course = Course(
        code=value["course_code"],
        name=value["course_name"],
        description=value["course_desc"],
        gpa=value["avg_gpa"],
        gpa_url=value["gpa_url"],
        enroll=value["avg_enroll"],
        profName=value["prof_name"],
        rmp=value["rmp"],
        rmp_url=value["prof_url"],
    )
    session.add(new_course)
    try:
        session.commit()
    except Exception as e:
        print(e)
        session.rollback()
print("Success")
