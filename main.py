import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle
from scipy.spatial import distance_matrix
from matplotlib.widgets import Button

# Parameters
num_points = 10  # Changed from 20 to 10
manual_points = 10  # This should equal num_points now
expansion_rate = 0.05
steps = 20
connection_threshold = 0.2
isolation_limit = 4  # Number of steps a circle can be isolated before stopping growth

# Add global states
paused = False
restart_requested = False
manual_points_list = []  # Store manually placed points
preview_artists = []  # Store preview circle and boundary for easy removal

# Add keyboard event handler
def on_key_press(event):
    global paused, restart_requested
    if event.key == ' ':  # Space bar
        paused = not paused
        plt.title(f"Step {step + 1} {'(PAUSED)' if paused else ''}")
        plt.draw()
    elif event.key == 'r':  # r key
        restart_requested = True
        paused = False

# Add mouse click handler
def on_click(event):
    global manual_points_list
    if event.inaxes == ax and len(manual_points_list) < manual_points:
        manual_points_list.append([event.xdata, event.ydata])
        
        # Clear previous plot
        ax.clear()
        ax.set_xlim(-1, 2)
        ax.set_ylim(-1, 2)
        
        # Redraw all points and their predictions
        for i, (x, y) in enumerate(manual_points_list):
            # Draw the actual circle (starting with radius 0)
            circle = Circle((x, y), 0, color='red', alpha=0.3)
            ax.add_patch(circle)
            
            # Draw predicted growth boundary
            predicted_radius = isolation_limit * expansion_rate
            predicted_circle = Circle((x, y), predicted_radius, 
                                   linestyle='--', 
                                   fill=False,
                                   color='red',
                                   alpha=0.5)
            ax.add_patch(predicted_circle)
            
            # Draw center point
            ax.plot(x, y, 'ko', markersize=5)
        
        if len(manual_points_list) == manual_points:
            plt.title("Starting simulation...")
        else:
            plt.title(f"Click to place point {len(manual_points_list) + 1}/{manual_points}")
        plt.draw()

def initialize_simulation():
    global manual_points_list
    # Convert manual points to numpy array - no random points needed
    points = np.array(manual_points_list)
    
    # Initialize circle radii and connections
    radii = np.zeros(num_points)
    connections = np.ones((num_points, num_points), dtype=bool)
    return points, radii, connections

# Move this function definition before the initial setup
def on_mouse_move(event):
    global preview_artists
    
    # Clear previous preview
    for artist in preview_artists:
        artist.remove()
    preview_artists = []
    
    # Only show preview if we're still accepting points
    if event.inaxes == ax and len(manual_points_list) < manual_points:
        # Create preview circle (starting radius 0)
        preview_circle = Circle((event.xdata, event.ydata), 0, 
                              color='red', alpha=0.15)
        ax.add_patch(preview_circle)
        preview_artists.append(preview_circle)
        
        # Create preview prediction boundary
        predicted_radius = isolation_limit * expansion_rate
        preview_prediction = Circle((event.xdata, event.ydata), 
                                 predicted_radius,
                                 linestyle='--',
                                 fill=False,
                                 color='red',
                                 alpha=0.25)
        ax.add_patch(preview_prediction)
        preview_artists.append(preview_prediction)
        
        # Add preview center point
        preview_point = ax.plot(event.xdata, event.ydata, 'ko', 
                              markersize=5, alpha=0.25)[0]
        preview_artists.append(preview_point)
        
    plt.draw()

# Move initial setup code after all function definitions
fig, ax = plt.subplots(figsize=(8, 8))
ax.set_aspect('equal')
fig.canvas.mpl_connect('key_press_event', on_key_press)
fig.canvas.mpl_connect('button_press_event', on_click)
fig.canvas.mpl_connect('motion_notify_event', on_mouse_move)

# Set initial plot limits
ax.set_xlim(-1, 2)
ax.set_ylim(-1, 2)
plt.title(f"Click to place point 1/{manual_points}")

# Wait for manual point placement
while len(manual_points_list) < manual_points:
    plt.pause(0.1)

# Initialize simulation with manual points
points, radii, connections = initialize_simulation()

# Set up plot
fig, ax = plt.subplots(figsize=(8, 8))
ax.set_aspect('equal')
fig.canvas.mpl_connect('key_press_event', on_key_press)

# Add array to track isolation
isolation_counts = np.zeros(num_points)  # Track how long each circle has been isolated

# Function to check and draw connections
def update_connections(ax, points, radii):
    global isolation_counts
    connected = np.zeros(num_points, dtype=bool)  # Track which points are connected this step
    
    for i in range(num_points):
        for j in range(i+1, num_points):
            if circles_overlap(points[i], points[j], radii[i], radii[j]):
                connections[i, j] = True
                connected[i] = True
                connected[j] = True
                ax.plot([points[i, 0], points[j, 0]], 
                       [points[i, 1], points[j, 1]], 
                       'k-', alpha=0.5)
    
    # Update isolation counts
    isolation_counts[~connected] += 1  # Increment count for isolated circles
    isolation_counts[connected] = 0    # Reset count for connected circles
    
    return connected  # Return connected status for prediction visualization

def circles_overlap(p1, p2, r1, r2):
    """Return True if two circles overlap"""
    dist = np.sqrt(((p1 - p2)**2).sum())
    return dist <= (r1 + r2)

# Main loop to expand circles and update connections
while True:  # Changed to infinite loop to allow restarts
    restart_requested = False
    points, radii, connections = initialize_simulation()
    isolation_counts = np.zeros(num_points)  # Reset isolation counts
    
    for step in range(steps):
        if restart_requested:
            break
            
        while paused:
            plt.pause(0.1)
            if restart_requested:
                break
        
        if restart_requested:
            break
            
        ax.clear()
        
        # Only expand circles that haven't been isolated too long
        active_circles = isolation_counts < isolation_limit
        radii[active_circles] += expansion_rate
        
        # Draw connections first (so they appear behind circles)
        for i in range(num_points):
            for j in range(i+1, num_points):
                if circles_overlap(points[i], points[j], radii[i], radii[j]):
                    ax.plot([points[i][0], points[j][0]], 
                           [points[i][1], points[j][1]], 
                           'k-', alpha=0.5)
        
        # Draw circles, center points, and predicted boundaries
        for i, (x, y) in enumerate(points):
            # Use different colors for active vs stopped circles
            is_active = isolation_counts[i] < isolation_limit
            color = "red" if is_active else "gray"
            
            # Draw the actual circle
            circle = Circle((x, y), radii[i], color=color, alpha=0.3)
            ax.add_patch(circle)
            
            # Draw predicted growth boundary
            if is_active:
                # Calculate predicted final radius
                predicted_radius = radii[i] + (isolation_limit - isolation_counts[i]) * expansion_rate
                predicted_circle = Circle((x, y), predicted_radius, 
                                       linestyle='--', 
                                       fill=False,
                                       color=color,
                                       alpha=0.5)
                ax.add_patch(predicted_circle)
            
            # Draw center point
            ax.plot(x, y, 'ko', markersize=5)
        
        # Update connections
        update_connections(ax, points, radii)
        
        # Set plot limits
        ax.set_xlim(-1, 2)
        ax.set_ylim(-1, 2)
        
        # Update title with isolation information
        isolated_count = np.sum(isolation_counts >= isolation_limit)
        plt.title(f"Step {step + 1} - {isolated_count} circles stopped {'(PAUSED)' if paused else ''}")
        plt.pause(1.0)
    
    if not restart_requested:
        break

plt.show()

plt.ion()  # Turn on interactive mode
