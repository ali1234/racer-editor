import numpy as np
from PySide6 import QtGui, QtWidgets


class Preview(QtWidgets.QLabel):
    def __init__(self, track):
        super().__init__()
        self.segment = 0
        self.px = 0
        self.py = 0
        self.track = track
        self.update_data()
        self._pixmap = QtGui.QPixmap(320, 240)
        self.redraw()
        self.track.visualChanged.connect(self.update_data)

    def move(self, d):
        self.py += d
        while self.py > self.L[self.segment]:
            self.py -= self.L[self.segment]
            self.segment += 1
            self.segment %= len(self.L)

    def update_data(self):
        self.P = self.track.P * 100
        self.M = self.track.M * 100
        self.A = self.track.A * 100
        self.B = self.track.B * 100
        self.L = np.linalg.norm(self.M, axis=1)
        self.segment %= len(self.P)

    def interpolate(self, seg, d):
        P = self.P[seg]
        M = self.M[seg]
        A = self.A[seg]
        B = self.B[seg]
        L = 1 / self.L[seg]
        t = d * L
        t2 = t**2
        t3 = t**3
        r = (A * t3) + (B * t2) + (M * t) + P
        dr = ((3*A)*t2) + ((2*B)*t) + M
        ddr = ((6*A)*t) + (2 * B)
        return r, dr * L, ddr * L * L

    def draw_lists(self):
        GROUND_HEIGHT = 120
        screenX = 160 + (self.px * 32)
        perspectiveDX = (160 - screenX) / GROUND_HEIGHT

        sy = np.empty((GROUND_HEIGHT, ), dtype=np.float32)
        sx = np.empty((GROUND_HEIGHT, ), dtype=np.float32)
        sz = np.empty((GROUND_HEIGHT, ), dtype=int)
        scale = np.empty((GROUND_HEIGHT, ))

        sp, sdp, sddp = self.interpolate(self.segment, self.py)
        camdir = sdp[:2] / np.linalg.norm(sdp[:2])
        camdir = np.array((camdir[1], -camdir[0]))

        for n in range(GROUND_HEIGHT):
            nn = n / (GROUND_HEIGHT - 1)
            z = 500 / (1.05 - nn)
            zz = 200 / z
            scale[n] = 1 - (nn / 1.01)
            py = self.py + z
            segment = self.segment
            while py > self.L[segment]:
                py -= self.L[segment]
                segment += 1
                segment %= len(self.L)

            p, dp, ddp = self.interpolate(segment, py)
            relpos = p - sp
            left = np.dot(relpos[:2], camdir) * zz
            sx[n] = left + screenX + (n * perspectiveDX)
            relh = relpos[2]
            sy[n] = relh * zz
            sz[n] = (int(py) % 512) > 255

        sy -= sy[0]
        y = np.linspace(239, 120, GROUND_HEIGHT) - sy

        return sx, scale, y.astype(int), sz

    def redraw(self):
        painter = QtGui.QPainter(self._pixmap)

        sky = QtGui.QColor(0, 200, 255)
        grass = QtGui.QColor(91, 173, 51), QtGui.QColor(81, 163, 41)
        road = QtGui.QColor(84, 66, 66), QtGui.QColor(74, 56, 56)
        curb = QtGui.QColor(200, 0, 0), QtGui.QColor(200, 200, 200)

        sx, ss, sy, sz = self.draw_lists()
        sx = sx[::-1]
        sy = list(sy[::-1]) + [240]
        ss = ss[::-1]
        sz = sz[::-1]

        painter.fillRect(0, 0, 320, 240, sky)

        for x, scale, y0, y1, c in zip(sx, ss, sy, sy[1:], sz):
            ya = min(y0, y1)
            yb = max(y0, y1)
            for y in range(ya, yb):
                painter.setPen(grass[c])
                painter.drawLine(0, y, 320, y)

                painter.setPen(road[c])
                l = x - (scale * 256)
                r = x + (scale * 256)
                painter.drawLine(l, y, r, y)

                painter.setPen(curb[c])
                curbw = scale*16
                painter.drawLine(l-curbw, y, l+curbw, y)
                painter.drawLine(r-curbw, y, r+curbw, y)

                if not c:
                    painter.setPen(curb[1])
                    dl = x - (scale * 4)
                    dr = x + (scale * 4)
                    painter.drawLine(dl, y, dr, y)

        self.setPixmap(self._pixmap)



