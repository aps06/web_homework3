import shutil
import os
import sys
import gzip
import concurrent.futures

def normalize(name_file):
    TRANS = {1072: 'a', 1040: 'A', 1073: 'b', 1041: 'B', 1074: 'v', 1042: 'V', 1075: 'g', 1043: 'G', 1076: 'd', 1044: 'D', 1077: 'e', 
             1045: 'E', 1105: 'e', 1025: 'E', 1078: 'j', 1046: 'J', 1079: 'z', 1047: 'Z', 1080: 'i', 1048: 'I', 1081: 'j', 1049: 'J', 
             1082: 'k', 1050: 'K', 1083: 'l', 1051: 'L', 1084: 'm', 1052: 'M', 1085: 'n', 1053: 'N', 1086: 'o', 1054: 'O', 1087: 'p', 
             1055: 'P', 1088: 'r', 1056: 'R', 1089: 's', 1057: 'S', 1090: 't', 1058: 'T', 1091: 'u', 1059: 'U', 1092: 'f', 1060: 'F', 
             1093: 'h', 1061: 'H', 1094: 'ts', 1062: 'TS', 1095: 'ch', 1063: 'CH', 1096: 'sh', 1064: 'SH', 1097: 'sch', 1065: 'SCH', 
             1098: '', 1066: '', 1099: 'y', 1067: 'Y', 1100: '', 1068: '', 1101: 'e', 1069: 'E', 1102: 'yu', 1070: 'YU', 1103: 'ya', 
             1071: 'YA', 1108: 'je', 1028: 'JE', 1110: 'i', 1030: 'I', 1111: 'ji', 1031: 'JI', 1169: 'g', 1168: 'G', 33: '_', 64: '_', 
             35: '_', 36: '_', 37: '_', 94: '_', 38: '_', 42: '_', 40: '_', 41: '_', 45: '_', 43: '_', 61: '_', 123: '_', 125: '_', 91: '_', 32: '_'}
    return name_file.translate(TRANS)


def run():
    if len(sys.argv) != 2:
        sys.exit(1)

    folder_sort = sys.argv[1]

    if not os.path.isdir(folder_sort):
        print(f"{folder_sort} is not a directory.")
        sys.exit(1)

    list_files, expansion = sort_file(folder_sort)

    return dec(list_files, expansion)


def dec(list_files, expansion):

    print('\n')

    for key, value in list_files.items():
        print(f"{key}:{value}")

    others_expansions = [os.path.splitext(others_expansion)[1] for others_expansion in list_files["other"] if True]

    print(f'\nexpansion: {expansion}\n\nothers_expansions: {others_expansions}')


def what_dir(file):

    name, suffix = os.path.splitext(file)

    if suffix.lower() in ['.jpeg', '.png', '.jpg', '.svg']:
        parameters = ['images', name, suffix, True,]

    elif suffix.lower() in ['.avi', '.mp4', '.mov', '.mkv']:
        parameters = ['video', name, suffix, True,]    

    elif suffix.lower() in ['.doc', '.docx', '.txt', '.pdf', 'xlsx', 'pptx']:
        parameters = ['documents', name, suffix, True]

    elif suffix.lower() in ['.mp3', '.ogg', '.wav', '.amr']:
        parameters = ['audio', name, suffix, True,]

    elif suffix.lower() in ['.zip', '.gz', '.tar']:
        parameters = ['archives', name, suffix, False,]

    else:
        parameters = ['other', name, suffix, True,]

    return parameters





def sort_file(parent_folder):

    file_names = {'images': [],
                  "video": [],
                  "documents": [],
                  "audio": [],
                  "archives": [],
                  "other": []}

    expansion = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:

        for folder in ['images', "video", "documents", "audio", "archives","other"]:
            try:
                executor.submit(os.mkdir, os.path.join(parent_folder, folder))
            except FileExistsError:
                pass

        for path_folder, folders, files in os.walk(parent_folder):

            for folder in ['images', "video", "documents", "audio", "archives", "other"]:
                try:
                    folders.remove(folder)
                except ValueError:
                    pass

            if files != []:

                for file in files:
                    parameters = what_dir(file)
                    file_names[parameters[0]].append(file)
                    expansion.append(parameters[2])
                    parameters[1] = normalize(parameters[1]) if parameters[3] else parameters[1]
                    create_path = os.path.join(parent_folder, parameters[0])

                    if parameters[0] in ['images', "video", "documents", "audio", 'other']:
                        executor.submit(shutil.move, os.path.join(path_folder, file), os.path.join(create_path, f'{parameters[1]}{parameters[2]}'))

                    elif parameters[0] == 'archives':
                        os.chdir(path_folder)
                        try:
                            if parameters[2].lower() != '.gz':
                                executor.submit(shutil.unpack_archive, file, os.path.join(create_path, parameters[1]))
                            else:
                                with gzip.open(file, 'rb') as file_in:
                                    with open(os.path.join(create_path, parameters[1]), 'wb') as file_out:
                                        executor.submit(shutil.copyfileobj, file_in, file_out)
                            os.remove(file)

                        except shutil.ReadError:
                            executor.submit(shutil.move, file, create_path)

                        finally:
                            os.chdir(parent_folder)

        for del_dir in os.listdir(parent_folder):

            if os.listdir(os.path.join(parent_folder, del_dir)) == [] or not del_dir  in ['images', "video", "documents", "audio", "archives", "other"]:
                shutil.rmtree(os.path.join(parent_folder, del_dir))

    return file_names, expansion


if __name__ == "__main__":

    run()
