#!/bin/bash
# -------------------------------------------------------------------------------------
#  Qualys Security TechServices Pvt. Ltd.
# -------------------------------------------------------------------------------------
#  Script name...: Yum_script.sh
#  Author........: Omkar Dhekne <odhekne@qualys.com>
#  Contact.......: Amit Doshi <adoshi@qualys.com>
#  Created on....: 2020-12-18
#  Last modified.: 2023-09-26
#  Purpose.......: Deployment script to apply security patches via Qualys Patch-Management module.
#  Revision......: v1.7
#  Status........: Active
# -------------------------------------------------------------------------------------

# Environment Variables:
    PACKAGE="${1}"
    PKGS_FOUND=""
    RES_FILE="${2}"
    TIMEOUT="${3}"
    ERR_FILE="${RES_FILE%json*}error"
    BASEPATH="${RES_FILE%/*}"

    # Package list to store associative array: installedCurrentVersionList, availableVersionList, installedPackageArchList
    IVPACKAGELIST="${BASEPATH}/installed_version_package_list.txt"
    IAPACKAGELIST="${BASEPATH}/installed_arch_package_list.txt"
    AVPACKAGELIST="${BASEPATH}/available_version_package_list.txt"

    # Condition to set YUM variable
    if [ -e /usr/bin/yum ]
    then
        YUM="/usr/bin/yum"
    elif [ -e /usr/bin/dnf ]
    then
        YUM="/usr/bin/dnf"
    fi

# Code:

    # This is pre-patch-deployment action to be run only once to generate required data.
    preaction()
    {
        if ! [[ -e "${IVPACKAGELIST}" ]] || ! [[ -e "${IAPACKAGELIST}" ]] || ! [[ -e "${AVPACKAGELIST}" ]]
        then
            # Enabled repository count.
            if ! [[ -e "${BASEPATH}/repocount.txt" ]]
            then
                ${YUM} repolist -v 2> /dev/null | awk '/Repo-baseurl/{print $3}' | wc -l > "${BASEPATH}/repocount.txt"
                CHECK_YUM_REPO="$(cat ${BASEPATH}/repocount.txt)"
                if [ "${CHECK_YUM_REPO}" == "0" ]
                then
                    CUSTOM_EXIT_CODE="3"
                    EXIT_CODE="1"
                    echo -e "${CHECK_YUM_REPO}\nPackage repository is not enabled on this system." > /dev/stderr
                    echo -e "{\"customExitCode\":${CUSTOM_EXIT_CODE}, \"exitCode\":${EXIT_CODE}}" > "${RES_FILE}"
                    exit "${EXIT_CODE}"
                fi
            else
                CHECK_YUM_REPO="$(cat "${BASEPATH}/repocount.txt")"
                if [ "${CHECK_YUM_REPO}" == "0" ]
                then
                    CUSTOM_EXIT_CODE="3"
                    EXIT_CODE="1"
                    echo -e "${CHECK_YUM_REPO}\nPackage repository is not enabled on this system." > /dev/stderr
                    echo -e "{\"customExitCode\":${CUSTOM_EXIT_CODE}, \"exitCode\":${EXIT_CODE}}" > "${RES_FILE}"
                    exit "${EXIT_CODE}"
                fi
            fi

            # Initialize array
            declare -A installedCurrentVersionList
            declare -A installedPackageArchList
            declare -A availablePatchVersionList

            # Generating the installed packages list (currently installed)
            INSTALLEDCURRENTVERSION="$(rpm -qa --qf="%{NAME}.%{ARCH},%{VERSION}-%{RELEASE}\n" | sed 's/(none)/none/g' | sort -u)"

            # Convert output to associative array.
            while IFS=',' read -r pkg version
            do
                if [[ -z "${installedCurrentVersionList[${pkg}]}" ]]
                then
                    installedCurrentVersionList[${pkg}]="${version}"
                else
                    installedCurrentVersionList[${pkg}]+=",${version}"
                fi
            done <<< "${INSTALLEDCURRENTVERSION}"

            # Add installedCurrentVersionList to installed_version_package_list.txt file
            declare -p installedCurrentVersionList > "${IVPACKAGELIST}"

            # Generating the architeture list for installed packages.
            INSTALLEDPACKAGEARCH="$(rpm -qa --qf="%{NAME},%{ARCH}\n" | sed 's/(none)/none/g' | sort -u)"

            # Convert output to associative array.
            while IFS=',' read -r pkg arch
            do
                installedPackageArchList[${pkg}]="${arch}"

            done <<< "${INSTALLEDPACKAGEARCH}"

            # Add installedPackageArchList to installed_arch_package_list.txt file
            declare -p installedPackageArchList > "${IAPACKAGELIST}"

            # Generating the available packages list (only including those base packages that exist in the installed package list and have a version higher than the currently installed package version)
            AVAILABLEPATCHVERSION="$(yum list available --showduplicates | column -t | grep -A999999 "^Available" | grep -v "Available" | awk '{print $1 "," $2}' | sed 's/[0-9][0-9]*://' | grep "^$(rpm -qa --qf="%{NAME}.%{ARCH}\n" | sed 's/(none)/none/g')" | sort -u)"

            # Convert output to associative array.
            while IFS=',' read -r pkg version
            do
                if [[ -z "${availablePatchVersionList[${pkg}]}" ]]
                then
                    availablePatchVersionList[${pkg}]="${version}"
                else
                    availablePatchVersionList[${pkg}]+=",${version}"
                fi
            done <<< "${AVAILABLEPATCHVERSION}"

            # Add availablePatchVersionList to available_version_package_list.txt file
            declare -p availablePatchVersionList > "${AVPACKAGELIST}"
        fi
    }

    # 1. If current time is greater than timout then mark as failure.
    # 2. When current time is less than timeout then yum process is already running.
    # 3. Wait for 300 seconds or 5 minutes to finish, once finished continue patch job.
    # 4. If yum process is still running, if yes then exit patch job and mark it as failure.

    check_yum_running()
    {
        # Current time in epoch / seconds.
        CURRENTTIME="$(date +%s)"
        # Exit code for command failure.
        EXIT_CODE="1"

        while [[ ${CURRENTTIME} -le ${TIMEOUT} ]]
        do
            # Yum command process id.
            YUM_PID="$(pgrep -x "${YUM}")"
            if [ -z "${YUM_PID}" ]
            then
                return
            fi

            sleep 300
            CURRENTTIME="$(date +%s)"
        done

        # Yum command to get process id.
        YUM_PID="$(pgrep -x "${YUM}")"
        if [ -z "${YUM_PID}" ]
        then
            return
        fi

        CUSTOM_EXIT_CODE="4"
        echo -e "Another application is currently holding the yum lock." > /dev/stderr
        echo -e "{\"customExitCode\":${CUSTOM_EXIT_CODE}, \"exitCode\":${EXIT_CODE}}" > "${RES_FILE}"
        exit "${EXIT_CODE}"
    }

    # 1. If repolist does not contains repos then mark as fail.
    # 2. If patch version matches within list of installed package versions then mark it as already installed.
    # 3. If patch version matches within list of available package versions then go ahead for patching.
    # 4. If patch version does not match with installed and available versions then mark it as not applicable (basically, pacakge not installed on the system).
    # 5. If patch architecture does not match with installed architecture and matches with list of available architectures then mark it as not applicable.

    check_installed_packages()
    {
        # Source data from package_list.txt
        source "${IVPACKAGELIST}" 2>/dev/null
        source "${IAPACKAGELIST}" 2>/dev/null
        source "${AVPACKAGELIST}" 2>/dev/null

        # Package name without '.rpm'.
        PKG="${PACKAGE%.rpm}"
        # Base package name, without version and architecture i.e. 'kernel'.
        PKG_BASE_NAME="$(printf "%s" "${PKG}" | rev | cut --complement -d'-' -f 1,2 | rev)"
        # Architecture string i.e. 'x86_64' or 'noarch'.
        ARCH="$(printf "%s" "${PKG}" | awk -F '.' '{print $(NF)}')"
        # Package with base package name and version without architecture i.e. 'kernel-4.1.0-el7_9'.
        PKG_BASE_WITHOUT_ARCH="${PKG%."${ARCH}"*}"
        # Package version i.e. '4.1.0-el7_9'.
        PKG_VERSION="$(printf "%s" "${PKG_BASE_WITHOUT_ARCH#*"${PKG_BASE_NAME}"-}" | sed 's/[0-9][0-9]*://')"
        # Exit code 1 for command failure.
        EXIT_CODE="1"

        # Architecture of installed package i.e. 'x86_64'.
        INSTALLED_ARCH="${installedPackageArchList["${PKG_BASE_NAME}"]}"
        # List of available architectures.
        AVAILABLE_ARCH="aarch64 noarch i386 i486 i586 i686 x86_64 s390 s390x ppc ppc64 ppc64le"
        # List of installed package versions i.e. '3.10.0-1160.88.1.el7 3.10.0-1160.90.1.el7 3.10.0-1160.95.1.el7'.
        INSTALLED_PKG_VERSION="${installedCurrentVersionList["${PKG_BASE_NAME}.${INSTALLED_ARCH}"]}"
        # List of available package versions i.e. '5.14.0-70.13.1.0.3.el9_0 5.14.0-70.17.1.0.1.el9_0'.
        LIST_OF_AVAILABLE_VERSIONS="$(echo -e "${availablePatchVersionList["${PKG_BASE_NAME}.${ARCH}"]}" | sed 's/,/ /g')"

        # Function to check whether patch version is lower or higher version than installed version.
        # Status 0 - lower patch version, Status 1 - higher patch version,
        # Status 2 - Either installed version is empty or/and patch arch does not match installed arch.

        {
            # Remove characters other than digits and separators such as dot, dash, underscore.
            local PATCH_VERSION="$(echo -e "${PKG_VERSION}" | sed 's/[^0-9._-]//g')"
            local INSTALLED_HIGHER="$(echo -e "${INSTALLED_PKG_VERSION}" | awk -F ',' '{print $NF}' | sed 's/[^0-9._-]//g')"

            # If installed version is not empty and package architecture is same as installed one, then go ahead.
            if [ -n "${INSTALLED_HIGHER}" ] && [ "${ARCH}" == "${INSTALLED_ARCH}" ]
            then
                # Read digits separated by either dot or dash or underscore and assign to parts1/2.
                IFS='._-' read -ra parts1 <<< "${PATCH_VERSION}"
                IFS='._-' read -ra parts2 <<< "${INSTALLED_HIGHER}"

                # Assign highest number of digits to length variable.
                if [ ${#parts1[@]} -gt ${#parts2[@]} ] || [ ${#parts1[@]} -eq ${#parts2[@]} ]
                then
                    length=${#parts1[@]}
                elif [ ${#parts1[@]} -lt ${#parts2[@]} ]
                then
                    length=${#parts2[@]}
                fi

                # Compare patch-version and installed version, to conclude higher or lower.
                # Empty part will be replaced by 0 during digit comparison to avoid syntax error.
                for ((i = 0; i < length; i++)); do
                    if (( 10#${parts1[i]:-0} < 10#${parts2[i]:-0} ))
                    then
                        LOWERVERSION="0" # LOWER
                        break
                    elif (( 10#${parts1[i]:-0} > 10#${parts2[i]:-0} ))
                    then
                        LOWERVERSION="1" # HIGHER
                        break
                    fi
                done
            else
                LOWERVERSION="2" # N/A
            fi
        }

        # Conditions to display exit code.
        if [[ -z "${INSTALLED_PKG_VERSION}" ]]
        then
            CUSTOM_EXIT_CODE="2"
            echo -e "Package \"${PKG_BASE_NAME}\" is not installed on the system." > /dev/stderr
            echo -e "{\"customExitCode\":${CUSTOM_EXIT_CODE}, \"exitCode\":${EXIT_CODE}}" > "${RES_FILE}"
            exit "${EXIT_CODE}"
        elif [[ "${ARCH}" != "${INSTALLED_ARCH}" ]] && [[ ("${ARCH}" != *"${AVAILABLE_ARCH}"*) ]]
        then
            CUSTOM_EXIT_CODE="2"
            echo -e "Package \"${PKG_BASE_NAME}\" with architecture \"${ARCH}\" is not applicable." > /dev/stderr
            echo -e "{\"customExitCode\":${CUSTOM_EXIT_CODE}, \"exitCode\":${EXIT_CODE}}" > "${RES_FILE}"
            exit "${EXIT_CODE}"
        elif [[ "${PKG_VERSION}" == "${INSTALLED_PKG_VERSION}" ]] && [[ "${ARCH}" == "${INSTALLED_ARCH}" ]]
        then
            CUSTOM_EXIT_CODE="1"
            echo -e "${INSTALLED_PKG_VERSION}\nPackage \"${PKG_BASE_NAME}\" with version \"${INSTALLED_PKG_VERSION}\" is already installed." > /dev/stderr
            echo -e "{\"customExitCode\":${CUSTOM_EXIT_CODE}, \"exitCode\":${EXIT_CODE}}" > "${RES_FILE}"
            exit "${EXIT_CODE}"
        elif [[ "${LOWERVERSION}" -eq 0 ]] && [[ ("${LIST_OF_AVAILABLE_VERSIONS}" == *"${PKG_VERSION}"*) ]]
        then
            CUSTOM_EXIT_CODE="1"
            echo -e "Package \"${PKG_BASE_NAME}\" with higher version \"${INSTALLED_PKG_VERSION}\" is already installed." > /dev/stderr
            echo -e "{\"customExitCode\":${CUSTOM_EXIT_CODE}, \"exitCode\":${EXIT_CODE}}" > "${RES_FILE}"
            exit "${EXIT_CODE}"
        elif [[ ("${LIST_OF_AVAILABLE_VERSIONS}" == *"${PKG_VERSION}"*) ]] && [[ "${ARCH}" == "${INSTALLED_ARCH}" ]]
        then
            PKGS_FOUND="${PKG}"
        elif [[ "${PKG_VERSION}" != "${INSTALLED_PKG_VERSION}" ]] && [[ ("${LIST_OF_AVAILABLE_VERSIONS}" != *"${PKG_VERSION}"*) ]]
        then
            CUSTOM_EXIT_CODE="2"
            echo -e "Package \"${PKG_BASE_NAME}\" with version \"${PKG_VERSION}\" is not available for patching." > /dev/stderr
            echo -e "{\"customExitCode\":${CUSTOM_EXIT_CODE}, \"exitCode\":${EXIT_CODE}}" > "${RES_FILE}"
            exit "${EXIT_CODE}"
        fi
    }

    # 1. If output is exited normally then mark it as success.
    # 2. If output is not exited normally then check for other conditions and mark it as failure or already installed.

    check_updates()
    {
        # Run package update.
        CMD="$(${YUM} -y update "${PKGS_FOUND}" 2> "${ERR_FILE}" ; printf "%s" "${?}")"
        # Standard output in lower case.
        CMD="${CMD,,}"
        # Standard error output.
        ERR="$(cat "${ERR_FILE}")"
        # Standard error output in lower case.
        ERR="${ERR,,}"

        # Conditions to display exit code.
        if [[ ("${CMD}" == *"upgraded:"*) ]] || [[ ("${CMD}" == *"updated:"*) ]] || [[ ("${CMD}" == *"installed:"*) ]]
        then
            CUSTOM_EXIT_CODE="0"
            EXIT_CODE="0"
            echo -e "${CMD}\nPackage \"${PKGS_FOUND}\" is successfully updated on the system." > /dev/stderr
            echo -e "{\"customExitCode\":${CUSTOM_EXIT_CODE}, \"exitCode\":${EXIT_CODE}}" > "${RES_FILE}"

            # Append updated packge version information to installedCurrentVersionList
            # Initialize array
            declare -A installedCurrentVersionList

            # Generating the installed packages list (currently installed)
            INSTALLEDCURRENTVERSION="$(rpm -qa --qf="%{NAME}.%{ARCH},%{VERSION}-%{RELEASE}\n" | sed 's/(none)/none/g' | sort -u)"

            # Convert output to associative array.
            while IFS=',' read -r pkg version
            do
                if [[ -z "${installedCurrentVersionList[${pkg}]}" ]]
                then
                    installedCurrentVersionList[${pkg}]="${version}"
                else
                    installedCurrentVersionList[${pkg}]+=",${version}"
                fi
            done <<< "${INSTALLEDCURRENTVERSION}"

            # Add installedCurrentVersionList to installed_version_package_list.txt file
            declare -p installedCurrentVersionList > "${IVPACKAGELIST}"

            exit "${EXIT_CODE}"
        elif [[ ("${ERR}" == *"could not retrieve"*) ]]
        then
            CUSTOM_EXIT_CODE="3"
            EXIT_CODE="1"
            echo -e "${CMD}\n${ERR}\nCannot proceed with the patch-job, please check Proxy/DNS config." > /dev/stderr
            echo -e "{\"customExitCode\":${CUSTOM_EXIT_CODE}, \"exitCode\":${EXIT_CODE}}" > "${RES_FILE}"
            exit "${EXIT_CODE}"
        elif [[ ("${CMD}" == *"nothing to do"*) ]] || [[ ("${CMD}" == *"no packages marked for update"*) ]]
        then
            CUSTOM_EXIT_CODE="1"
            EXIT_CODE="1"
            echo -e "${CMD}\n${ERR}\nPackage \"${PKG_BASE_NAME}\" with higher version \"${INSTALLED_PKG_VERSION}\" is already installed." > /dev/stderr
            echo -e "{\"customExitCode\":${CUSTOM_EXIT_CODE}, \"exitCode\":${EXIT_CODE}}" > "${RES_FILE}"
            exit "${EXIT_CODE}"
        else
            CUSTOM_EXIT_CODE="3"
            EXIT_CODE="1"
            echo -e "${CMD}\n${ERR}" > /dev/stderr
            echo -e "{\"customExitCode\":${CUSTOM_EXIT_CODE}, \"exitCode\":${EXIT_CODE}}" > "${RES_FILE}"
            exit "${EXIT_CODE}"
        fi
    }

# Execute Functions:
    preaction
    check_yum_running
    check_installed_packages
    check_updates

# Remove error file:
    rm -f "${ERR_FILE}"



