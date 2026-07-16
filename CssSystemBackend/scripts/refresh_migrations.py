import os


def delete_migration_files():
    for root, dirs, files in os.walk(os.getcwd()):
        if os.path.basename(root) == "migrations":
            for file in files:
                if file != "__init__.py" and file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    print(f"Deleting: {file_path}")
                    os.remove(file_path)
                elif file.endswith(".pyc"):
                    file_path = os.path.join(root, file)
                    print(f"Deleting: {file_path}")
                    os.remove(file_path)


if __name__ == "__main__":
    delete_migration_files()
