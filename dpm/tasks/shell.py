"""System-level instructions."""

from subprocess import check_output as os_check_output
from subprocess import CalledProcessError


class Shell:
    """Convenient interface to the Linux shell."""

    def __init__(self):
        pass

    @classmethod
    def check_output(cls, instruction):
        """Utility interface of `subprocess.check_output`.

        Will sanatize output by attempting to decode the data to 'utf-8' format,
        strip all strings, and will not return empty-strings in a list.

        Type-marshalling, validation, etc. are the responsibility of the user.

        Args:
            instruction (str, list): `subprocess.check_output` takes either a
                string or joinable-list as input.

        Returns:
            output (str, list): Attempts to return a string, but returns a list
                of strings if multiple have been found.
        """

        try:
            output = os_check_output(instruction, shell=True).decode('utf-8').split('\n')

            # Sanatized returns:
            if isinstance(output, str):
                return output.strip()

            output.remove('')
            if output.__len__() == 1:
                return output[0].strip()

            return [s.strip() for s in output]
        except CalledProcessError:
            pass
            #raise CalledProcessError    # TODO: exception-handling

    @classmethod
    def os_id(cls):
        """Attempt to identify the distributor of the OS by various means.

        Returns:
            title (str): identifier of the OS."""

        title = Shell.check_output('lsb_release -d')
        if title:
            return title.replace('Description:', '').strip()

        title = Shell.check_output('uname -r')
        if title:
            return title.split('-')[-1]
