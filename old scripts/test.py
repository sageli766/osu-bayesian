from osrparse import Replay
from osupyparser import OsuFile
from osupyparser.osu.objects import Circle, Slider, Spinner
from osrparse.utils import Key, Mod
from osrparse import ReplayEventOsu
from SliderObject import toVector2, toVector2List, SliderObject
from stacking import stacking_fix
import math
import numpy as np
import pandas as pd

sr_dict = {'BLOODY_RED': 7.14, 'EXTRA': 6.41, 'EXPERT': 5.61, 'gmtn': 6.54}
pp_dict = {
            'razorfruit':15078,
            # 'shaun':10196,
            'YukiTanuki':9210,
            'WEIRD FACE':8881,
            # 'guibbs':6905,
            # 'worst ez player':6755,
            '-Axolotl':11672,
            # 'Kazemiya':8756,
            'My Angel Sayaka':6984,
            'owoMaxx':11000,
            'Piemanray314':7837,
            'sweatily':10153,
            'Texas':8178,
            # 'nano desu':8847
}

pp_dict_lobotomy = {
            'razorfruit':15078,
            'shaun':10196,
            'guibbs':6905,
            'worst_ez_player':6755,
            '-Axolotl':11672,
            'nano_desu':8847,
            'Kazemiya': 8756
}

# user = 'razorfruit'
# diff = 'EXPERT'
#
# replay_name = f"./replays/{user}_{diff}.osr"
# map_name = f"{diff}.osu"
# enable_hardrock = False
# enable_EZ = False
#
# player_pp = 15078
# player_id = user
# map_id = diff
# map_sr = sr_dict[map_id]
# error_distance = []
# jump_distance = [0]
#
# coords_hit = []
# objects_hit = []
#
# coords_miss = []
# objects_miss = []
#
# coords = []
# objects = []

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
        if self.head.time == time:
            self.head.data.replaydata = data
            return

        curr = self.head
        while curr.next is not None:
            curr = curr.next
            if curr.time == time:
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
    fix_list = []
    total_time = 0
    hits = 0
    last_time = -999999999
    ownership_dict = {}

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

    for i in range(len(all_objects)):
        object = all_objects[i]

        if isinstance(object, Spinner):
            continue

        chunks = chunked_replay(replay_blocks, last_time=last_time, lower_bound=object.start_time - window,
                                upper_bound=object.start_time + window)
        candidates = []

        for curr in chunks:
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
                    candidates.append(curr)

        for candidate in candidates:
            if candidate in ownership_dict.values():
                continue
            else:
                ownership_dict[object.start_time] = candidate
                hits += 1
                last_time = candidate.data.time
                if isinstance(object, Slider):
                    temp = slider_break(curr.next, object)
                    for t in temp:
                        fix_list.append(t)

                #GETTING COORDINATES OF HIT AND STORING IT IN COORDS LIST
                test = ownership_dict[object.start_time]
                test_x = test.data.replaydata.__getattribute__('x')
                test_y = test.data.replaydata.__getattribute__('y')
                coords_hit.append([test_x, test_y])

                test_obj_x = object.pos.x
                test_obj_y = object.pos.y
                objects_hit.append([test_obj_x, test_obj_y])

                coords.append([test_x, test_y])
                objects.append([test_obj_x, test_obj_y])
                break


if __name__ == '__main__':
    # for user in list(pp_dict_lobotomy.keys()):
    for user in ['Kazemiya']:
        for diff in ['BLOODY_RED', 'EXPERT', 'EXTRA']:
            print(f'Now processing:{user}')

            replay_name = f"./replays_lobotomy/{user}_{diff}.osr"
            map_name = f"{diff}.osu"
            enable_hardrock = False
            enable_EZ = False

            player_pp = pp_dict_lobotomy[user]
            player_id = user
            map_id = diff
            map_sr = sr_dict[map_id]
            error_distance = []
            jump_distance = [0]

            coords = []
            objects = []

            coords_hit = []
            objects_hit = []

            coords_miss = []
            objects_miss = []

            replay = Replay.from_path(replay_name)
            data = OsuFile(map_name).parse_file()
            replay_data = replay.replay_data
            timing_points = data.timing_points
            flip = False if Mod.HardRock in replay.mods else True
            if enable_hardrock:
                replay.mods = replay.mods | Mod.HardRock
            elif enable_EZ:
                replay.mods = replay.mods | Mod.Easy
            #replay.mods = Mod.NoMod
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
            # all_objects = stacking_fix(data.hit_objects, data, radius, enable_hardrock)
            #all_objects = typescript_new_stacking_heights(data.hit_objects, data, radius, enable_hardrock)
            print('loading objects')
            misses = replay_fix(window_50, iteration=False)

            iterations = 1
            while misses > 0 and iterations < 1:
                replay = Replay.from_path("flarg.osr")
                data = OsuFile(map_name).parse_file()
                replay_data = replay.replay_data
                misses = replay_fix(window_50, iteration=True)
                iterations += 1
            if misses > 0:
                pass
                # print('couldnt fix miss after 3 iterations')

            # print(f"coords: {coords_hit}, len: {len(coords_hit)}")
            # print(f"objects: {objects_hit}, len: {len(objects_hit)}")
            #
            # print(f"miss coords: {coords_miss}, len: {len(coords_miss)}")
            # print(f"miss objects: {objects_miss}, len: {len(objects_miss)}")

            for coord, object in zip(coords, objects):
                x1, y1 = object
                x2, y2 = coord
                dist = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                error_distance.append(dist)

            for i in range(len(objects) - 1):
                x1, y1 = objects[i]
                x2, y2 = objects[i+1]
                dist = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
                jump_distance.append(dist)

            # print(f"hit errors: {error_distance}")
            # print(f"jump dist: {jump_distance}")

            assert len(error_distance) == len(jump_distance)

            columns = ['player_id', 'player_pp', 'map_sr', 'map_id', 'error_distance', 'jump_distance']
            output = pd.DataFrame(data=np.zeros((len(error_distance[::8]), 6)), columns=columns)

            output['error_distance'] = error_distance[::8]
            output['jump_distance'] = jump_distance[::8]
            output['player_id'] = player_id
            output['player_pp'] = player_pp
            output['map_sr'] = map_sr
            output['map_id'] = map_id

            output.to_csv(path_or_buf=f'./data/{user}_{diff}.csv')
