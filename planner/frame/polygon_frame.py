from planner.frame import Figure
from svgwrite import shapes


_lt = lambda a, b: (a[0] < b[0]) or ((a[0] == b[0]) and (a[1] < b[1]))
norm = lambda vec: (vec[0] ** 2 + vec[1] ** 2) ** .5

class PolygonFrame(Figure):

    """
    Polygon figure.
    """

    DEFAULT_ATTRIBS = {"stroke": "#000", "stroke-width": "2", "fill": "#fff", "fill-rule": "evenodd"}
    BORDER_ATTRIBS = {"stroke": "#000", "stroke-width": "2", "fill-opacity": "0"}

    def __init__(self, points, wall_width=1, **attribs):
        """
        `points` - iterable with tuples of coordinates (x, y)
        """
        self.points = points
        self.length = len(points)
        self.wall_width = wall_width
        self.attribs = self.DEFAULT_ATTRIBS.copy()
        self.attribs.update(attribs)
        # Warning! must be minimum 3 point
        assert self.length >= 3
        self.scale_coeff = 0.88

        # calculate self inner points
        self._sort_points()
        self._get_internal_points()


    def _draw(self):
        res = []
        border_attribs = self.BORDER_ATTRIBS.copy()
        border_attribs.update(self.attribs)

        backround_attribs = self.attribs.copy()
        del backround_attribs['stroke']
        del backround_attribs['stroke-width']

        backround_poly = [self.points[0]]
        backround_poly.extend(self.inner_points)
        backround_poly.append(self.inner_points[0])
        backround_poly.extend(self.points)
        res.append(shapes.Polygon(backround_poly, **backround_attribs))


        res.append(shapes.Polygon(self.points, **border_attribs))
        border_attribs['stroke'] = 'red'
        res.append(shapes.Polygon(self.inner_points, **border_attribs))
        border_attribs['stroke'] = 'green'
        self._homothetic_transform()
        res.append(shapes.Polygon(self.inner_points, **border_attribs))

        return res

    def _sort_points(self):
        """ Find top left point and set is first """
        base_point = self.points[0]
        base_index = 0
        for index, point in enumerate(self.points):
            if _lt(point, base_point):
                base_point = point
                base_index = index
        # rotate points
        self.points = self.points[base_index:] + self.points[:base_index]

    def _homothetic_transform(self):
        """ Calculate inner polygon points """
        inner_points = []

        x = (self.points[0][0] * self.scale_coeff, self.points[0][1] * self.scale_coeff)
        mk = self._move_corner(0)
        shift = mk[0] - x[0], mk[1] - x[1] 

        for point in self.points:
            inner_points.append((
                point[0] * self.scale_coeff + shift[0],
                point[1] * self.scale_coeff + shift[1]))
        self.inner_points = inner_points

    def _get_internal_points(self):
        """ Calculate inner polygon points """
        inner_points = []

        for index in range(self.length):
            inner_points.append(self._move_corner(index))
        self.inner_points = inner_points

    def _move_corner(self, index):
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
        det = [1, -1][det < 0]
        ort_o = ort_o[0] * det, ort_o[1] * det
        # calculate distance
        distance = (ort_o[0] * self.wall_width, ort_o[1] * self.wall_width)
        control_point = (O[0] + distance[0], O[1] + distance[1])
        return control_point
