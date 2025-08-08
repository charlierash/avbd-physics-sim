# AVBD Physics Simulation (using PyMunk)

import pygame
import pymunk
import sys
import pygame_gui

class Camera:
    def __init__(self, screen_width, screen_height):
        self.pan = pygame.Vector2(screen_width / 2, screen_height / 2)
        self.zoom = 1.0
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.pan_speed = 15
        self.zoom_speed = 0.1

    def handle_input(self, keys, events):
        # Pan
        if keys[pygame.K_w]:
            self.pan.y -= self.pan_speed / self.zoom
        if keys[pygame.K_s]:
            self.pan.y += self.pan_speed / self.zoom
        if keys[pygame.K_a]:
            self.pan.x -= self.pan_speed / self.zoom
        if keys[pygame.K_d]:
            self.pan.x += self.pan_speed / self.zoom

        # Zoom
        for event in events:
            if event.type == pygame.MOUSEWHEEL:
                if event.y > 0:
                    self.zoom *= (1 + self.zoom_speed)
                else:
                    self.zoom *= (1 - self.zoom_speed)
                self.zoom = max(0.1, self.zoom)

    def world_to_screen(self, world_pos):
        screen_center = pygame.Vector2(self.screen_width / 2, self.screen_height / 2)
        return (pygame.Vector2(world_pos.x, world_pos.y) - self.pan) * self.zoom + screen_center

    def screen_to_world(self, screen_pos):
        screen_center = pygame.Vector2(self.screen_width / 2, self.screen_height / 2)
        return (pygame.Vector2(screen_pos[0], screen_pos[1]) - screen_center) / self.zoom + self.pan

class GUI:
    def __init__(self, manager, screen_width):
        self.manager = manager
        self.panel = pygame_gui.elements.UIPanel(relative_rect=pygame.Rect((screen_width - 320, 0), (320, 720)),
                                                  starting_height=0,
                                                  manager=self.manager)

        self.sliders = {}
        self.buttons = {}
        self.labels = {}

        self.create_global_settings()
        self.create_box_settings()
        self.create_buttons()

    def create_global_settings(self):
        self.labels['global_title'] = pygame_gui.elements.UILabel(relative_rect=pygame.Rect((10, 10), (280, 25)), text='Global Settings', manager=self.manager, container=self.panel)
        self.sliders['delta_time'] = self.create_slider('Delta Time', 20, 0, 1/30, 1/60)
        self.sliders['iterations'] = self.create_slider('Iterations', 60, 1, 20, 10, is_int=True)
        self.sliders['gravity'] = self.create_slider('Gravity', 100, 0, 2000, 981)

    def create_box_settings(self):
        self.labels['box_title'] = pygame_gui.elements.UILabel(relative_rect=pygame.Rect((10, 160), (280, 25)), text='New Box Properties', manager=self.manager, container=self.panel)
        self.sliders['box_size_x'] = self.create_slider('Box Size X', 180, 10, 200, 50, is_int=True)
        self.sliders['box_size_y'] = self.create_slider('Box Size Y', 220, 10, 200, 50, is_int=True)
        self.sliders['friction'] = self.create_slider('Friction', 260, 0, 2, 0.5)
        self.sliders['velocity_x'] = self.create_slider('Velocity X', 300, -500, 500, 0)
        self.sliders['velocity_y'] = self.create_slider('Velocity Y', 340, -500, 500, 0)
        self.sliders['bounciness'] = self.create_slider('Bounciness', 380, 0, 2, 0.5)

    def create_buttons(self):
        self.buttons['reset'] = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((10, 440), (140, 30)), text='Reset', manager=self.manager, container=self.panel)
        self.buttons['pause'] = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((160, 440), (140, 30)), text='Pause', manager=self.manager, container=self.panel)

    def create_slider(self, name, y_pos, min_val, max_val, start_val, is_int=False):
        pygame_gui.elements.UILabel(relative_rect=pygame.Rect((10, y_pos), (100, 25)), text=name, manager=self.manager, container=self.panel)
        slider = pygame_gui.elements.UIHorizontalSlider(relative_rect=pygame.Rect((110, y_pos), (180, 25)),
                                                        start_value=start_val,
                                                        value_range=(min_val, max_val),
                                                        manager=self.manager,
                                                        container=self.panel)
        slider.is_int = is_int
        return slider

    def get_value(self, slider_name):
        slider = self.sliders[slider_name]
        if slider.is_int:
            return int(slider.get_current_value())
        return slider.get_current_value()

def create_box(space, pos, size=(50, 50), mass=1, friction=0.5, elasticity=0.5, velocity=(0,0)):
    moment = pymunk.moment_for_box(mass, size)
    body = pymunk.Body(mass, moment)
    body.position = pos
    body.velocity = velocity
    shape = pymunk.Poly.create_box(body, size)
    shape.friction = friction
    shape.elasticity = elasticity
    space.add(body, shape)
    return body

def draw_bodies(screen, space, camera):
    for body in space.bodies:
        for shape in body.shapes:
            if isinstance(shape, pymunk.Segment):
                p1 = camera.world_to_screen(body.local_to_world(shape.a))
                p2 = camera.world_to_screen(body.local_to_world(shape.b))
                pygame.draw.line(screen, (0, 0, 0), p1, p2, int(max(1, shape.radius * 2 * camera.zoom)))
            elif isinstance(shape, pymunk.Poly):
                verts = [camera.world_to_screen(body.local_to_world(v)) for v in shape.get_vertices()]
                if len(verts) > 2:
                    pygame.draw.polygon(screen, (100, 100, 200), verts)
                    pygame.draw.polygon(screen, (50, 50, 100), verts, 2)

def main():
    pygame.init()

    screen_width = 1280
    screen_height = 720
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("AVBD Physics Simulation")
    clock = pygame.time.Clock()

    manager = pygame_gui.UIManager((screen_width, screen_height))
    gui = GUI(manager, screen_width)

    space = pymunk.Space()
    space.gravity = (0, gui.get_value('gravity'))
    space.iterations = gui.get_value('iterations')

    camera = Camera(screen_width, screen_height)

    boxes = []

    # Floor
    floor_body = pymunk.Body(body_type=pymunk.Body.STATIC)
    floor_shape = pymunk.Segment(floor_body, (-5000, screen_height), (5000, screen_height), 5)
    floor_shape.friction = 1.0
    space.add(floor_body, floor_shape)

    paused = False
    selected_body = None
    drag_stiffness = 6000
    drag_damping = 200

    running = True
    while running:
        time_delta = clock.tick(60)/1000.0

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == gui.buttons['reset']:
                        for box in boxes:
                            if box in space.bodies:
                                space.remove(box, box.shapes[0])
                        boxes.clear()
                    if event.ui_element == gui.buttons['pause']:
                        paused = not paused
                        gui.buttons['pause'].set_text('Resume' if paused else 'Pause')

            if not manager.process_events(event):
                if event.type == pygame.MOUSEBUTTONDOWN:
                    world_pos = camera.screen_to_world(pygame.mouse.get_pos())
                    if event.button == 1: # Left click to drag
                        shape_info = space.point_query_nearest(world_pos, 0, pymunk.ShapeFilter())
                        if shape_info and shape_info.shape.body.body_type == pymunk.Body.DYNAMIC:
                            selected_body = shape_info.shape.body
                    elif event.button == 2: # Middle click to spawn
                        box_body = create_box(space, world_pos,
                                              size=(gui.get_value('box_size_x'), gui.get_value('box_size_y')),
                                              friction=gui.get_value('friction'),
                                              elasticity=gui.get_value('bounciness'),
                                              velocity=(gui.get_value('velocity_x'), gui.get_value('velocity_y')))
                        boxes.append(box_body)
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1 and selected_body:
                        selected_body = None

        keys = pygame.key.get_pressed()
        camera.handle_input(keys, events)

        # Handle dragging and deleting
        mouse_pressed = pygame.mouse.get_pressed()
        if selected_body:
            mouse_world_pos = camera.screen_to_world(pygame.mouse.get_pos())
            vec = mouse_world_pos - selected_body.position
            force = vec * drag_stiffness
            damping_force = -selected_body.velocity * drag_damping
            total_force = force + damping_force
            selected_body.apply_force_at_world_point(total_force, selected_body.position)

        to_be_removed = set()
        if mouse_pressed[2] and not manager.get_focus_set(): # Right click to delete
            world_pos = camera.screen_to_world(pygame.mouse.get_pos())
            shape_info = space.point_query_nearest(world_pos, 0, pymunk.ShapeFilter())
            if shape_info and shape_info.shape.body.body_type == pymunk.Body.DYNAMIC:
                body_to_remove = shape_info.shape.body
                if body_to_remove in boxes:
                    to_be_removed.add(body_to_remove)

        for body in to_be_removed:
            if body in space.bodies:
                space.remove(body, *body.shapes)
            if body in boxes:
                boxes.remove(body)

        manager.update(time_delta)

        # Update physics
        if not paused:
            dt = gui.get_value('delta_time')
            space.gravity = (0, gui.get_value('gravity'))
            space.iterations = gui.get_value('iterations')
            space.step(dt)

        # Drawing
        screen.fill((200, 200, 200))
        draw_bodies(screen, space, camera)
        manager.draw_ui(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
