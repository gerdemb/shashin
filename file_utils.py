import shutil


def path_file_walk(path):
    if path.is_file():
        yield path
    else:
        for child in sorted(path.iterdir()):
            if child.is_file():
                yield child
            elif child.is_dir():
                # TODO make configurable
                if child.name != '@eaDir':
                    yield from path_file_walk(child)


def is_child(parent, child):
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def action_required(file, dest_path):
    # This assertion should never happen, but is included to prevent unintended data loss by accidentally
    # overwriting files
    assert dest_path.is_dir() or not dest_path.exists()

    return file.parent != dest_path


def check_destination(file, dest_path):
    # Check that file with identical name doesn't already exist in dest_path
    return not (dest_path / file.name).exists()


def file_operation(cmd, file, dest_path):
    dest_path.mkdir(parents=True, exist_ok=True)
    return cmd(str(file), str(dest_path))


def mv(file, dest_path):
    if check_destination(file, dest_path):
        return file_operation(shutil.move, file, dest_path)


def cp(file, dest_path):
    if check_destination(file, dest_path):
        return file_operation(shutil.copy2, file, dest_path)


def nop(file, dest_path):
    if check_destination(file, dest_path):
        return dest_path / file.name


def print_action(action, *args):
    action_ljust = action.ljust(8)
    print(f"[{action_ljust}] " + " ".join([str(a) for a in args]))