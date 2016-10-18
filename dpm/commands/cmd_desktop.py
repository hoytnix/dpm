"""Interface of the Linux command-line utility 'xdotool' which simulates the
desktop-window environment."""

import json
from os import path

import click

from dpm.tasks.fs import local_directory
from dpm.tasks.shell import Shell


class Desktop:
    """An interface to the Linux command-line utility `xdotool` to provide
       utilities for the Xorg-desktop."""

    def __init__(self):
        self.desktops = {}

    def restore(self):
        """Emulate a store to represent the local desktop-environment."""

        self.load()
        for desktop_number in self.desktops:
            desktop = self.desktops[desktop_number]    # Convenience pointer.
            for window in desktop:
                w = Window(title=window['title'])
                w.set_dimensions(window['dimensions'])
                w.set_position(window['position'])

    def snapshot(self):
        """Populate the store and dump it."""

        self.populate_desktops()
        self.dump()

    def load(self):
        """Load a desktop-environment from a Json-file."""

        cfg_file = local_directory(path='desktop/desktops.json')
        with open(cfg_file, 'r') as stream:
            self.desktops = json.load(stream)

    def dump(self):
        """Dump the current desktop-environment to a Json-file."""

        data_directory = local_directory(path='desktop')
        if not path.exists(data_directory):
            import os
            os.makedirs(data_directory)

        cfg_file = local_directory(path='desktop/desktops.json')
        with open(cfg_file, 'w+') as stream:
            json.dump(obj=self.desktops, fp=stream, indent=4)

    def populate_desktops(self):
        """Iterate the desktop-windows and populate their values with their
        respective classmethod-properties."""

        _, desktop_range = Desktop.virtual_desktops()
        for desktop_number in desktop_range:
            self.desktops[str(desktop_number)] = []

        window_ids = Desktop.window_ids()
        for window_id in window_ids:
            window = Window(window_id=window_id)
            self.desktops[window.desktop_number].append(window.store)

    @classmethod
    def virtual_desktops(cls):
        """Provides a count and range for the number of virtual-desktops in the
        current Xorg-environment.

        Additionally determines the lower/upper-bounds to return in the range.

        Returns:
            tuple:
                desktops (int): A natural-number representation of the number of
                    virtual desktops available.
                desktops_range (range): A determinable python-range which
                    represents the computer's counting of the desktops.
        """

        desktops = Shell.check_output('xdotool get_num_desktops')
        desktops = int(desktops)    # pylint: disable=redefined-variable-type

        desktop_zero_start = Shell.check_output('xdotool search --desktop 0 --name ".*"')
        if desktop_zero_start:
            desktops_range = range(desktops)
        else:
            desktops_range = range(1, desktops + 1)

        return (desktops, desktops_range)

    @classmethod
    def window_ids(cls):
        """Returns a list of all windows available while also filtering empty
        desktops.

        Returns:
            list:
                window_ids
        """

        window_ids = []
        _, desktops_range = cls.virtual_desktops()
        for desktop_number in desktops_range:
            desktop_windows = Shell.check_output(
                'xdotool search --desktop {} --name ".*"'.format(desktop_number))
            if desktop_windows:    # Returns False if the desktop has no windows
                for window_id in desktop_windows:
                    window_ids.append(window_id)
        return window_ids


class Window:
    """Window is as-defined by the X11-Window-System.

    This class provides a utility to access local-properties of a window.

    Args:
        window_id (str, int-like): The identifier of the window on the system.
        title (str): If provided, a window_id will be found, if possible.
    """

    def __init__(self, window_id=None, title=None):
        if window_id:
            self.window_id = window_id
        else:
            self.window_id = Window.search(title)

        self.store = {
            'title': self.title,
            'position': self.position(),
            'dimensions': self.dimensions()
        }

    @classmethod
    def unmaximize(cls, title):
        """Removes all maximized window-decorators.

        Args:
            title (str): the search string to pass to wmctrl.
        """

        instruction = 'wmctrl -r "{}" -b remove,maximized_vert,maximized_horz' \
            .format(title)
        Shell.check_output(instruction)

    def set_position(self, position):
        """Modify the xy position of a window.

        Args:
            position (dict): {x}{y} coordinates.
        """

        Window.unmaximize(title=self.title)
        Shell.check_output('xdotool windowmove {} {x} {y}'.format(self.window_id, **
                                                                  position))

    def set_dimensions(self, dimensions):
        """Modify the width and heigth dimensions of a window.

        Args:
            dimensions (dict): {w}idth and {h}eigth.
        """

        Window.unmaximize(title=self.title)
        Shell.check_output('xdotool windowsize {} {w} {h}'.format(self.window_id, **
                                                                  dimensions))

    @classmethod
    def search(cls, title):
        """Search for a window-id by using the title."""

        id_results = Shell.check_output('xdotool search --name "%s"' % title)
        if isinstance(id_results, str):
            return id_results
        else:
            for id_result in id_results:
                try:
                    result_title = Shell.check_output('xdotool getwindowname {}'
                                                      .format(id_result))
                except:    # pylint: disable=bare-except
                    continue

                if result_title:
                    if title in result_title:
                        return id_result

    @property
    def title(self):
        """Call 'xdotool getwindowname {self.window_id}'.

        Returns:
            title (str)
        """

        return Shell.check_output('xdotool getwindowname %s' % self.window_id)

    @property
    def desktop_number(self):
        """Call 'xdotool get_desktop_for_window {self.window_id}'.

        Returns:
            desktop (str, int-like): the Xorg virtual-desktop number the window
                has been assigned to. Compatible with `desktops_range`.
        """

        return Shell.check_output('xdotool get_desktop_for_window {}'.format(
            self.window_id))

    @property
    def geometry(self):
        """Call 'xdotool getwindowgeometry {self.window_id}'.

        Returns:
            geometry (list, len=3)
            False: if the self.window_id is not found.
        """

        return Shell.check_output('xdotool getwindowgeometry {}' \
                                                        .format(self.window_id))

    def position(self):
        """Return the x and y screen coordinates of a window.

        Args:
            geometry (Desktop.window_geometry)

        Returns:
            {x, y} (dict-strings, int-like): X and Y coordinates.
        """

        x, y = self.geometry[1].replace('Position: ', '') \
                .replace(' (screen: 0)', '').split(',')
        return {'x': x, 'y': y}

    def dimensions(self):
        """Strips the width and heigth of a window from an xdotool-geometry
        call.

        Args:
            geometry (Desktop.window_geometry)

        Returns:
            {w, h} (dict-strings, int-like): Width and heigth.
        """

        w, h = self.geometry[2].replace('Geometry: ', '').split('x')
        return {'w': w, 'h': h}


@click.group()
def cli():
    """ Xorg utility. """
    pass


@cli.command()
def snapshot():
    d = Desktop()
    d.snapshot()


@cli.command()
def restore():
    d = Desktop()
    d.restore()
