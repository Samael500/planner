from planner.frame.figure import Figure
from planner.frame.polygon import Polygon
from svgwrite import shapes


_lt = lambda a, b: (a[0] < b[0]) or ((a[0] == b[0]) and (a[1] < b[1]))
norm = lambda vec: (vec[0] ** 2 + vec[1] ** 2) ** .5

class PolygonFrame(Figure):

    """
    Polygon figure.
    """

    DEFAULT_ATTRIBS = {"stroke": "#000", "stroke-width": "2", "fill": "#fff", "fill-rule": "evenodd"}
    BORDER_ATTRIBS = {"stroke": "#000", "stroke-width": "2", "fill-opacity": "0"}

    def __init__(self, points, distance=1, homothetic_transform=True, **attribs):
        """
        `points` - iterable with tuples of coordinates (x, y)
        """
        self.points = points
        self.length = len(points)
        self.distance = distance
        self.attribs = self.DEFAULT_ATTRIBS.copy()
        self.attribs.update(attribs)
        # Warning! must be minimum 3 point
        assert self.length >= 3

        # calculate self inner points
        self._sort_points()
        self._homothetic_transform() if homothetic_transform else self._get_internal_points()

        self.apertures = []
        self.stroke_width = attribs.get('stroke-width') or self.DEFAULT_ATTRIBS.get('stroke-width')
        self.stroke = attribs.get('stroke') or self.DEFAULT_ATTRIBS.get('stroke')


    def _draw(self):
        res = []
        border_attribs = self.BORDER_ATTRIBS.copy()
        border_attribs.update(self.attribs)
        backround_attribs = self.attribs.copy()

        # Hatching and filling
        if hasattr(self, "hatch") and self.hatch:
            backround_attribs['style'] = "fill: url(#{})".format(self._hatching_id)
            res.append(self.hatch)
        if hasattr(self, "filling"):
            backround_attribs['fill'] = self.filling
        else:
            if 'fill' not in backround_attribs:
                backround_attribs['fill'] = "#fff"

        del backround_attribs['stroke']
        del backround_attribs['stroke-width']

        # Create outer and inner polygons
        backround_poly = []
        backround_poly.append(self.points[0])
        backround_poly.extend(self.inner_points)
        backround_poly.append(self.inner_points[0])
        backround_poly.extend(self.points)

        # backround
        res.append(shapes.Polygon(backround_poly, **backround_attribs))
        # Apertures
        if self.apertures:
            for aperture in self.apertures:
                res.append(aperture._draw())
        # borders
        res.append(shapes.Polygon(self.points, **border_attribs))
        # border_attribs['stroke'] = 'red'
        res.append(shapes.Polygon(self.inner_points, **border_attribs))

        return res

    def _sort_points(self):
        """ Find top left point and set is first """
        base_point = self.points[0]
        base_index = 0
        max_x, max_y = min_x, min_y = base_point
        for index, point in enumerate(self.points):
            if _lt(point, base_point):
                base_point = point
                base_index = index
            min_x = min(point[0], min_x)
            min_y = min(point[1], min_y)
            max_x = max(point[0], max_x)
            max_y = max(point[1], max_y)
        # rotate points
        self.points = self.points[base_index:] + self.points[:base_index]
        # calculate mid point
        self.mid = (min_x + max_x) / 2, (min_y + max_y) / 2

    def _homothetic_transform(self):
        """ Calculate inner polygon points """
        inner_points = []

        point = self.points[0]
        corner = self._move_corner(0, False)

        inner = corner[0] - self.mid[0], corner[1] - self.mid[1]
        outer = point[0] - self.mid[0], point[1] - self.mid[1]
        scale_coeff =  norm(inner) / norm(outer)

        distance = point[0] * scale_coeff, point[1] * scale_coeff
        shift = corner[0] - distance[0], corner[1] - distance[1] 

        for point in self.points:
            inner_points.append((
                point[0] * scale_coeff + shift[0],
                point[1] * scale_coeff + shift[1]))
        self.inner_points = inner_points

    def _get_internal_points(self):
        """ Calculate inner polygon points """
        inner_points = []

        for index in range(self.length):
            inner_points.append(self._move_corner(index))
        self.inner_points = inner_points

    def _move_corner(self, index, clock=True):
        """ Calculate distance between external and internal corner """
        A, O, B = self.points[index - 1], self.points[index], self.points[(index + 1) % self.length]
        # calculate ort's vectors
        vec_a = (A[0] - O[0], A[1] - O[1])
        ort_a = (vec_a[0] / norm(vec_a), vec_a[1] / norm(vec_a))
        vec_b = (B[0] - O[0], B[1] - O[1])
        ort_b = (vec_b[0] / norm(vec_b), vec_b[1] / norm(vec_b))
        # calculate bissectriss
        vec_o = (ort_a[0] + ort_b[0], ort_a[1] + ort_b[1])
        ort_o = (vec_o[0] / norm(vec_o), vec_o[1] / norm(vec_o))
        # get angle sign
        det = vec_b[0] * vec_a[1] - vec_b[1] * vec_a[0]
        det = [1, -1][det < 0] if clock else 1
        ort_o = ort_o[0] * det, ort_o[1] * det
        # calculate distance
        distance = (ort_o[0] * self.distance, ort_o[1] * self.distance)
        control_point = (O[0] + distance[0], O[1] + distance[1])
        return control_point

    def add_aperture(self, points, **attribs):
        """
        Add aperture (door, window, etc) to the wall.
        points - coordinates of aperture polygon
        """
        # Propagate stroke and stroke-width
        if 'stroke-width' not in attribs:
            attribs['stroke-width'] = self.stroke_width
        if 'stroke' not in attribs:
            attribs['stroke'] = self.stroke

        aperture = Polygon(points, **attribs)
        self.apertures.append(aperture)
        return aperture
