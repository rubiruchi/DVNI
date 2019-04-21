from mininet.log import info

from container import Docker
from utils.document import add_hyperlink


# TODO: Discuss and fix issues with network card ordering:
# https://unix.stackexchange.com/questions/10254/how-to-change-the-order-of-the-network-cards-eth1-eth0-on-linux

class Kali(Docker):
    # Static varible for ports.
    # Avoids using these numbers elsewhere in code where it may become confusing.
    VNC_DEFAULT = 5900
    WEB_DEFAULT = 6080

    started = False
    packages_to_install = list()

    def __init__(self, name, resolution="1920x1080x24", vnc=VNC_DEFAULT, web=WEB_DEFAULT, **kwargs):
        """
            Creates a Kali host running a VNC server and NoVNC web server

            :param resolution: (Optional) String in the format WidthxHeightxColorDepth for the remote display.
            :type resolution: string
            :param vnc: Port to bind VNC to on the host.
            :type vnc: int
            :param web: Port to bind NoVNC web server to on the host.
            :type web: int
        """
        # Init environment settings if none have been passed
        if 'environment' not in kwargs:
            kwargs['environment'] = {}
        # Set resolution in environment settings from parameter if not set
        if 'RESOLUTION' not in kwargs['environment']:
            kwargs['environment']['RESOLUTION'] = resolution
        Docker.__init__(self,
                        name,
                        dimage="kali",
                        dcmd="/init",
                        ports=[Kali.VNC_DEFAULT, Kali.WEB_DEFAULT],
                        port_bindings={Kali.VNC_DEFAULT: vnc, Kali.WEB_DEFAULT: web},
                        publish_all_ports=True,
                        **kwargs)

    def config(self, **kwargs):
        super(Kali, self).config(**kwargs)
        # Install collected packages
        self._install_package(self.packages_to_install)
        self.started = True

    def add_package(self, *packages):
        """
        Adds required packages to the kali box. Packages are installed when starting the network.

        :param packages:
        :type packages: [string]
        """
        # If the host isn't started, add packages to a list for later
        if not self.started:
            self.packages_to_install += packages
        else:
            self._install_package(list(packages))

    def _install_package(self, packages):
        """
        Internal function that installs packages. Use add_package instead to add packages.
        """
        # Return if theres nothing to install
        if len(packages) == 0:
            return
        info("*** Installing Kali packages\n")
        self.cmd("apt install -y", " ".join(packages))

    def add_hint(self, doc):
        """
        Appends a hint to the supplied document, telling users how to connect to this machine.

        :param doc: The word document to add a hint to.
        :type doc: Document
        """
        p = doc.add_paragraph('Connect to port ')
        p.add_run(str(self.port_bindings[Kali.VNC_DEFAULT])).bold = True
        p.add_run(' with VNC or view the webpage ')
        add_hyperlink(p, 'http://10.10.0.1:%d/vnc_auto.html?port=%d' % (
            self.port_bindings[Kali.WEB_DEFAULT], self.port_bindings[Kali.VNC_DEFAULT]), "here")
        p.add_run(' with a web browser to access to Kali machine for this task.')
        doc.add_paragraph().add_run(
            'NOTE: Many tools will use the default interface of eth0, the network for tasks is %s' % self.defaultIntf()).bold = True


def example():
    from mininet.log import setLogLevel
    from mininet.clean import cleanup
    from mininet.net import Containernet
    from mininet.cli import CLI

    setLogLevel('debug')

    cleanup()

    net = Containernet(controller=None)

    kali = net.addDocker('kali',
                         cls=Kali,
                         resolution="1920x1080x24",  # OPTIONAL
                         port_vnc=5900,  # OPTIONAL
                         port_web=6080,  # OPTIONAL
                         ip='10.10.10.1/24')
    kali.add_package("nmap")
    kali.add_package("iproute2", "dnmap")

    h1 = net.addHost('h1',
                     ip='10.10.10.2/24')
    s1 = net.addSwitch('s1')

    net.addLink(h1, s1)
    net.addLink(kali, s1)

    net.start()

    CLI(net)
    net.stop()


if __name__ == "__main__":
    example()
