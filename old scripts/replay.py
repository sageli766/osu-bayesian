from osrparse import Replay
from osupyparser import OsuFile
from osupyparser.osu.objects import Circle, Slider, Spinner
from osrparse.utils import Key, Mod
from osrparse import ReplayEventOsu
from SliderObject import toVector2, toVector2List, SliderObject
from stacking import stacking_fix
import math


replay_name = "shaun.osr"
map_name = "shaun.osu"
enable_hardrock = False
enable_EZ = False

class ReplayTime:
    def __init__(self, replaydata, time):
        self.replaydata = replaydata
        self.time = time


class Node:
    def __init__(self, data):
        self.data = data
        self.prev = None
        self.next = None


class doubly_linked_list:
    def __init__(self):
        self.head = None

    def append(self, data):
        if self.head is None:
            self.head = Node(data)
            return
        curr = self.head
        while curr.next is not None:
            curr = curr.next
        new_node = Node(data)
        new_node.prev = curr
        curr.next = new_node

    def replace(self, time, data):
        if self.head.data.time == time:
            self.head.data.replaydata = data
            return

        curr = self.head
        while curr.next is not None:
            curr = curr.next
            if curr.data.time == time:
                curr.data.replaydata = data
                return

    def print_list(self):
        curr = self.head
        while curr is not None:
            print(f'{curr.data.replaydata}, {curr.data.time}')
            curr = curr.next


def chunked_replay(arr, last_time, lower_bound, upper_bound):
    chunks = []
    curr = arr.head
    last = last_time if last_time > lower_bound else lower_bound
    while curr is not None:
        if last <= curr.data.time <= upper_bound:
            chunks.append(curr)
        curr = curr.next
    return chunks


def find_hit(prev_hit, curr_hit):
    if curr_hit <= 0:
        return False

    if (Key.K1 in prev_hit and Key.K2 in prev_hit) and (Key.K1 in curr_hit and Key.K2 not in curr_hit):
        return False
    elif (Key.K1 in prev_hit and Key.K2 in prev_hit) and (Key.K1 not in curr_hit and Key.K2 in curr_hit):
        return False
    elif prev_hit == curr_hit:
        return False

    if prev_hit <= 0 and (Key.K1 in curr_hit or Key.K2 in curr_hit):
        return True
    elif Key.K1 in prev_hit and Key.K2 in curr_hit:
        return True
    elif Key.K2 in prev_hit and Key.K1 in curr_hit:
        return True

def stack_leniency(hit_objects):
    approach_time_window = 1800 - 120 * approach_rate
    stack_time_window = approach_time_window * (data.stack_leniency if data.stack_leniency else 7)
    shift_value = 3.5
    shift_list = {}

    if Mod.HardRock in replay.mods:
        for i in range(len(hit_objects)):
            y = hit_objects[i].pos.y
            if y > 192:
                y = y + 2 * (192 - y)
            else:
                y = y - 2 * (192 - (384 - y))
            hit_objects[i].pos.y = y

    for i in range(len(hit_objects) - 1, -1, -1):
        for j in range(i - 1, -1, -1):
            if hit_objects[i].start_time - hit_objects[j].start_time <= stack_time_window:
                if hit_objects[i].pos.x == hit_objects[j].pos.x and hit_objects[i].pos.y == hit_objects[j].pos.y:
                    if i in shift_list.keys():
                        shift_list[j] = shift_list[i] - shift_value
                    else:
                        shift_list[j] = 0
                        shift_list[j] -= shift_value
                    break
            else:
                break

    for i in range(len(hit_objects)):
        if i in shift_list.keys():
            hit_objects[i].pos.x += shift_list[i]
            hit_objects[i].pos.y += shift_list[i]
    return hit_objects

def slider_break(curr, slider):

    if slider.curve_type == 'Pass-Through':
        return []

    slider_chunks = []
    points = slider.points
    points.insert(0, slider.pos)
    test = SliderObject(toVector2(slider.pos), slider.start_time,
                        slider.curve_type, toVector2List(points),
                        slider.repeat_count, slider.pixel_length,
                        slider.duration, slider.end_time)
    test.CreateCurves()

    while curr.data.time < slider.start_time:
        curr = curr.next

    if slider.repeat_count > 1:
        end = .75
        r_mult = 1
    else:
        end = .75
        r_mult = 3

    closest_idx = 0
    for i in range(len(timing_points)):
        pt = timing_points[i]
        if slider.start_time >= pt.offset:
            closest_idx = i
        else:
            break

    velocity = timing_points[closest_idx].velocity

    for i in range(closest_idx, -1, -1):
        if timing_points[i].beat_length > 0:
            bl = timing_points[i].beat_length
            break

    dur = slider.repeat_count * ((bl * slider.pixel_length) / (data.slider_multiplier * 100 * velocity))
    while curr is not None and (curr.data.time - slider.start_time) / dur <= end:
        if slider.repeat_count == 1:
            te = (curr.data.time - slider.start_time) / dur
            slider_ball = test.PositionAtTime(te)
        else:
            repeats = slider.repeat_count
            te = repeats * ((curr.data.time - slider.start_time) / dur)
            aw = 1 - abs(1 - (te % 2))
            slider_ball = test.PositionAtTime(aw)


        if (curr.data.replaydata.__getattribute__('x') - slider_ball.x)**2 + (curr.data.replaydata.__getattribute__('y') - slider_ball.y) ** 2 > (radius * r_mult) ** 2:
            slider_chunks.append(ReplayTime(ReplayEventOsu(curr.data.replaydata.time_delta, slider_ball.x, slider_ball.y, Key.K1 | Key.M1), curr.data.time))
        elif curr.data.replaydata.__getattribute__('keys') == no_key:
            slider_chunks.append(ReplayTime(
                ReplayEventOsu(curr.data.replaydata.time_delta, curr.data.replaydata.__getattribute__('x'), curr.data.replaydata.__getattribute__('y'), Key.K1 | Key.M1), curr.data.time))
        # else:
        #     slider_chunks.append(ReplayTime(
        #         ReplayEventOsu(curr.data.replaydata.time_delta, curr.data.replaydata.__getattribute__('x'),
        #                        curr.data.replaydata.__getattribute__('y'), Key.K1 | Key.M1), curr.data.time))

        curr = curr.next

    return slider_chunks


def replay_fix(window, iteration) -> int:
    new_replay_data = []
    fix_list = []
    total_time = 0
    hits = 0
    misses = 0
    object_hit = False
    last_time = -999999999
    ownership_dict = {}
    #hit_or_miss = -999999999

    for object in all_objects:
        if object.start_time not in ownership_dict.keys():
            ownership_dict[object.start_time] = 0
    replay_blocks = doubly_linked_list()

    for event in replay_data:
        total_time += event.time_delta
        if enable_hardrock and flip and not iteration:
            event_x = event.__getattribute__('x')
            event_y = event.__getattribute__('y')
            if event_y > 192:
                event_y = event_y + 2 * (192 - event_y)
            else:
                event_y = event_y - 2 * (192 - (384 - event_y))
            event = ReplayEventOsu(event.time_delta, event_x, event_y, event.__getattribute__('keys'))

        replay_blocks.append(ReplayTime(event, total_time))

    # for i in range(1, len(all_objects)):
    #     prev_object = all_objects[i - 1]
    #     curr_object = all_objects[i]
    #     miss_time = None
    #     early_miss = chunked_replay(replay_blocks, last_time=-9999, lower_bound=prev_object.start_time - 400,
    #                                 upper_bound=prev_object.start_time - window)
    #     for curr in early_miss:
    #         prev_keys = no_key if curr.prev is None else curr.prev.data.replaydata.__getattribute__(
    #             'keys')
    #         replay_chunk = curr.data.replaydata
    #
    #         if curr.data.replaydata.time_delta == 0 and curr.prev is not None and curr.prev.data.replaydata.time_delta == 0:
    #             continue
    #
    #         key = find_hit(prev_keys, replay_chunk.__getattribute__('keys'))
    #         if key:
    #             miss_time = curr.data.time
    #             break
    #
    #     if miss_time is not None:
    #         lower = miss_time if miss_time > curr_object.start_time - 400 else curr_object.start_time - 400
    #         cleaning = chunked_replay(replay_blocks, last_time=-9999, lower_bound=lower, upper_bound=curr_object.start_time - window)
    #         for curr in cleaning:
    #
    #             prev_keys = no_key if curr.prev is None else curr.prev.data.replaydata.__getattribute__(
    #                 'keys')
    #             replay_chunk = curr.data.replaydata
    #             if curr.data.replaydata.time_delta == 0 and curr.prev is not None and curr.prev.data.replaydata.time_delta == 0:
    #                 continue
    #             replay_blocks.replace(curr.data.time, ReplayEventOsu(replay_chunk.time_delta, replay_chunk.__getattribute__('x'),
    #                                                       replay_chunk.__getattribute__('y'), no_key))


    for i in range(len(all_objects)):
        object = all_objects[i]

        if isinstance(object, Spinner):
            continue

        # if isinstance(object, Slider) and object.repeat_count > 1:
        #     chunks = chunked_replay(replay_blocks, last_time=last_time, lower_bound=object.start_time - window,
        #                             upper_bound=object.start_time)
        # else:
        #     chunks = chunked_replay(replay_blocks, last_time=last_time, lower_bound=object.start_time - window,
        #                         upper_bound=object.start_time + window)

        #last = hit_or_miss if hit_or_miss > object.start_time - window - 400 else object.start_time - window - 400
        #early = chunked_replay(replay_blocks, last_time=-9999, lower_bound=last,
        #                        upper_bound=object.start_time - window)
        # for curr in early:
        #     prev_keys = no_key if curr.prev is None else curr.prev.data.replaydata.__getattribute__('keys')
        #     replay_chunk = curr.data.replaydata
        #     if curr.data.replaydata.time_delta == 0 and curr.prev is not None and curr.prev.data.replaydata.time_delta == 0:
        #         continue
        #     key = find_hit(prev_keys, replay_chunk.__getattribute__('keys'))
        #     if key:
        #         replay_blocks.replace(curr.data.time, ReplayEventOsu(replay_chunk.time_delta, replay_chunk.__getattribute__('x'),replay_chunk.__getattribute__('y'), no_key))


        chunks = chunked_replay(replay_blocks, last_time=last_time, lower_bound=object.start_time - window,
                                upper_bound=object.start_time + window)
        candidates = []

        for curr in chunks:
            object_hit = False
            prev_keys = no_key if curr.prev is None else curr.prev.data.replaydata.__getattribute__('keys')
            replay_chunk = curr.data.replaydata

            if curr.data.replaydata.time_delta == 0 and curr.prev is not None and curr.prev.data.replaydata.time_delta == 0:
                continue

            key = find_hit(prev_keys, replay_chunk.__getattribute__('keys'))
            if not key:
                continue
            else:
                x = object.pos.x
                y = object.pos.y

                chunk_x = replay_chunk.__getattribute__('x')
                chunk_y = replay_chunk.__getattribute__('y')

                if (chunk_x - x) ** 2 + (chunk_y - y) ** 2 < (radius) ** 2:
                    # print('hit')
                    # hits += 1
                    # object_hit = True
                    # break
                    candidates.append(curr)

        for candidate in candidates:
            if candidate in ownership_dict.values():
                continue
            else:
                ownership_dict[object.start_time] = candidate
                object_hit = True
                hits += 1
                last_time = candidate.data.time
                #hit_or_miss = last_time
                if isinstance(object, Slider):
                    temp = slider_break(curr.next, object)
                    if len(temp) > 0:
                        for t in temp:
                            fix_list.append(t)
                        hit_or_miss = fix_list[-1].time
                break

        if not object_hit:
            misses += 1
            print(f'miss: {object.start_time} at {object.pos.x}, {object.pos.y}')
            if ownership_dict[object.start_time] != 0:
                replay_chunk = ownership_dict[object.start_time].data.replaydata
                previous = ownership_dict[object.start_time].prev
                x = object.pos.x
                y = object.pos.y

                chunk_x = replay_chunk.__getattribute__('x')
                chunk_y = replay_chunk.__getattribute__('y')
                #print(
                #    f'object {x},{y}\ncursor {chunk_x},{chunk_y}\n{(chunk_x - x) ** 2 + (chunk_y - y) ** 2} <= {radius ** 2}')

                fix_list.append(ReplayTime(ReplayEventOsu(previous.data.replaydata.time_delta, x, y, no_key), previous.data.time))

                fix_list.append(ReplayTime(ReplayEventOsu(replay_chunk.time_delta, x, y, replay_chunk.__getattribute__('keys')),curr.data.time))
                ownership_dict[object.start_time] = fix_list.append(ReplayTime(ReplayEventOsu(replay_chunk.time_delta, x, y, replay_chunk.__getattribute__('keys')), curr.data.time))
                #hit_or_miss = curr.data.time
                if isinstance(object, Slider):
                    temp = slider_break(ownership_dict[object.start_time].next, object)
                    if len(temp) > 0:
                        for t in temp:
                            fix_list.append(t)
                        #hit_or_miss = fix_list[-1].time
                break
            else:
                closest_chunk_to_obj = chunks[0]
                for curr in chunks[1:]:
                    if abs(object.start_time - curr.data.time) < abs(
                            object.start_time - closest_chunk_to_obj.data.time):
                        closest_chunk_to_obj = curr

                prev_obj = all_objects[i - 1]
                if ownership_dict[prev_obj.start_time] != 0 and ownership_dict[prev_obj.start_time].data.time == closest_chunk_to_obj.data.time:
                    closest_chunk_to_obj = closest_chunk_to_obj.next.next
                y = object.pos.y
                if closest_chunk_to_obj.prev is not None:
                    fix_list.append(ReplayTime(ReplayEventOsu(closest_chunk_to_obj.prev.data.replaydata.time_delta, object.pos.x, y, no_key), closest_chunk_to_obj.prev.data.time))
                fix_list.append(ReplayTime(ReplayEventOsu(closest_chunk_to_obj.data.replaydata.time_delta, object.pos.x, y, Key.K1 | Key.M1), closest_chunk_to_obj.data.time))

                closest_chunk_to_obj.data.replaydata = ReplayEventOsu(closest_chunk_to_obj.data.replaydata.time_delta, object.pos.x, y, Key.K1 | Key.M1)
                ownership_dict[object.start_time] = closest_chunk_to_obj
                #hit_or_miss = closest_chunk_to_obj.data.time
                if isinstance(object, Slider):
                    temp = slider_break(closest_chunk_to_obj.next, object)
                    if len(temp) > 0:
                        for t in temp:
                            fix_list.append(t)
                        #hit_or_miss = fix_list[-1].time


    curr = replay_blocks.head
    time_list = []
    while curr is not None:
        curr_time = curr.data.time
        if curr_time < all_objects[0].start_time:
            curr = curr.next
            continue
        if len(new_replay_data) == 0:
            new_replay_data.append(ReplayEventOsu(curr_time - curr.data.replaydata.time_delta, 192, 192, no_key))
            time_list.append(curr_time - curr.data.replaydata.time_delta)
            #curr = curr.prev
            break
        curr = curr.next


    while curr is not None:
        curr_time = curr.data.time

        for i in range(len(fix_list)):
            fix = fix_list[i]
            fix_time = fix.time
            if curr_time == fix_time and fix_time not in time_list:
                new_replay_data.append(fix_list[i].replaydata)
                time_list.append(fix_time)


                break
        if curr_time not in time_list:
            new_replay_data.append(curr.data.replaydata)
            time_list.append(curr_time)


        curr = curr.next

    # print(data.hit_objects)

    replay.replay_data = new_replay_data
    replay.write_path("flarg.osr")

    print(f'hits:{hits} misses:{misses} total:{hits + misses}')
    return misses


if __name__ == '__main__':
    replay = Replay.from_path(replay_name)
    data = OsuFile(map_name).parse_file()
    replay_data = replay.replay_data
    timing_points = data.timing_points
    flip = False if Mod.HardRock in replay.mods else True
    if enable_hardrock:
        replay.mods = replay.mods | Mod.HardRock
    elif enable_EZ:
        replay.mods = replay.mods | Mod.Easy


    cs = data.cs
    od = data.od
    ar = data.ar
    if Mod.HardRock in replay.mods:
        cs = data.cs * 1.3 if data.cs * 1.3 < 10 else 10
        od = data.od * 1.3 if data.od * 1.3 < 10 else 10
        ar = data.ar * 1.3 if data.ar * 1.3 < 10 else 10
    elif Mod.Easy in replay.mods:
        cs = data.cs / 2
        od = data.od / 2
        ar = data.ar / 2


    radius = 54.4 - 4.48 * cs
    window_300 = 80 - 6 * od
    window_100 = 140 - 8 * od
    window_50 = 200 - 10 * od
    approach_rate = ar
    no_key = replay_data[0].__getattribute__('keys')
    #all_objects = stack_leniency(data.hit_objects)
    all_objects = stacking_fix(data.hit_objects, data, radius, enable_hardrock)
    #all_objects = typescript_new_stacking_heights(data.hit_objects, data, radius, enable_hardrock)
    print('loading objects')
    misses = replay_fix(window_50, iteration=False)

    iterations = 1
    while misses > 0 and iterations < 3:
        replay = Replay.from_path("flarg.osr")
        data = OsuFile(map_name).parse_file()
        replay_data = replay.replay_data
        misses = replay_fix(window_50, iteration=True)
        iterations += 1
    if misses > 0:
        print('couldnt fix miss after 3 iterations')
        # iterations = 0
        # while misses > 0 and iterations < 3:
        #     replay = Replay.from_path("flarg.osr")
        #     data = OsuFile(map_name).parse_file()
        #     replay_data = replay.replay_data
        #     misses = replay_fix(window_100, iteration=True)
        #     iterations += 1

