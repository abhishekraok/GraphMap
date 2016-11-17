import cStringIO
import random
import time
import urllib2
from datetime import datetime


class TileTimeStat:
    def __init__(self, x, y, z, time_taken_ms, http_code, time_of_request):
        self.x = x
        self.y = y
        self.z = z
        self.time_taken_ms = time_taken_ms
        self.http_code = http_code
        self.time_of_request = time_of_request

    def __repr__(self):
        return 'TileTimeStat({},{},{},{} ms. HTTP {})'.format(self.x, self.y, self.z, self.time_taken_ms,
                                                              self.http_code)

    def to_tsv(self):
        return '\t'.join(str(i) for i in [self.x, self.y, self.z, self.time_taken_ms, self.http_code,
                                          self.time_of_request.strftime("%Y%m%d-%H%M%S")])


class AverageTimeStats:
    def __init__(self, tile_time_stats_list, end_point):
        """

        :type tile_time_stats_list: list of TileTimeStat
        """
        self.tile_time_stats_list = tile_time_stats_list
        self._average_time_ms = None
        self.end_point = end_point

    def calc_average_time_ms(self):
        if self._average_time_ms is None:
            self._average_time_ms = float(sum(i.time_taken_ms for i in self.tile_time_stats_list
                                              if i.http_code is not 404)) \
                                    / len(self.tile_time_stats_list)
        return self._average_time_ms

    def __str__(self):
        return 'Average time for {} tiles is {}'.format(len(self.tile_time_stats_list), self.calc_average_time_ms())

    def serialize_to_string(self):
        return (self.end_point + '\t' + i.to_tsv() + '\n' for i in self.tile_time_stats_list)

    def append_to_file(self, filename=None):
        if filename is None:
            header = '\t'.join(['End Point', 'x', 'y', 'z', 'time taken in ms', 'http code', 'time of request']) + '\n'
            final_filename = 'time_stats' + time.strftime("%Y%m%d-%H%M%S") + '.tsv'
        else:
            final_filename = filename
            header = ''
        print('Appending to file {} end point {}'.format(final_filename, self.end_point))
        with open(final_filename, 'a') as f:
            f.write(header)
            f.writelines(self.serialize_to_string())
        return final_filename


def generate_multiple_random_tiles(count, max_lod):
    tile_list = []
    for i in xrange(count):
        z = random.randint(0, max_lod)
        x = random.randint(0, 2 ** z)
        y = random.randint(0, 2 ** z)
        tile_list.append((x, y, z))
    return tile_list


class PerfTester:
    def __init__(self, endpoint=None, verbose=False):
        self.end_point = endpoint or 'http://localhost:5555'
        self.verbose = verbose

    def tile_url(self, x, y, z):
        return self.end_point + '/tile/{}/{}/{}'.format(z, x, y)

    def measure_xyz(self, x, y, z):
        url = self.tile_url(x, y, z)
        start_time = time.time()
        http_code = 200
        time_of_request = datetime.now()
        try:
            tile_image_io = cStringIO.StringIO(urllib2.urlopen(url).read())
        except urllib2.HTTPError as e:
            if e.code == 404:
                http_code = 404
        end_time = time.time()
        time_taken_ms = round((end_time - start_time) * 10 ** 3, 2)
        tile_stat = TileTimeStat(x, y, z, time_taken_ms, http_code, time_of_request)
        if self.verbose:
            print(tile_stat)
        return tile_stat

    def repeat_measure_xyz(self, x, y, z, repeat=3):
        stats = []
        for i in range(repeat):
            ts = self.measure_xyz(x, y, z)
            stats.append(ts)
            if ts.http_code == 404:
                return stats
            time.sleep(0.1)
        return stats

    def test_multiple_tiles(self, tile_list_to_hit):
        all_stats = []
        for tile in tile_list_to_hit:
            all_stats.extend(self.repeat_measure_xyz(*tile))
        return all_stats

    def test_random_tiles(self, count, max_lod):
        tiles_to_hit = generate_multiple_random_tiles(count, max_lod)
        all_stats = self.test_multiple_tiles(tiles_to_hit)
        return AverageTimeStats(all_stats, self.end_point)

def test_local(count=100):
    print('localhost')
    local_performance_tester = PerfTester(verbose=True)
    avg_local = local_performance_tester.test_random_tiles(count, 20)
    print(avg_local)
    avg_local.append_to_file()

def test_kaii(count=100):
    print('kaiimap')
    kaiimap_performance_tester = PerfTester(endpoint='http://kaiimap.org', verbose=True)
    avg_kaii = kaiimap_performance_tester.test_random_tiles(count, 20)
    print (avg_kaii)
    avg_kaii.append_to_file()

if __name__ == '__main__':
    test_kaii(1000)
