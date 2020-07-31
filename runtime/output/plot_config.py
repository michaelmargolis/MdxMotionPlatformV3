import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def plot(base_pos, platform_pos, platform_mid_height, PLATFORM_NAME ):
    base_labels = ['base{0}'.format(i) for i in range(6)]
    platform_labels = ['platform{0}'.format(i) for i in range(6)]
    if PLATFORM_NAME == "Flying Platform":
       is_flying_platform = True
       img = plt.imread("flying_platform.png")
       plt.imshow(img, zorder=1, extent=[-600, 600, -600, 600])
    else:
        is_flying_platform = False
        img = plt.imread("chair_red.png")
        plt.imshow(img, zorder=1, extent=[-400, 400, -400, 400])
        
    bx= base_pos[:,0]
    by = base_pos[:,1]
    plt.scatter(bx,by,zorder=2)
    
    px= platform_pos[:,0]
    py = platform_pos[:,1]
    plt.axis('equal')
    plt.scatter(px,py,zorder=3)
    # plt.imshow(img, zorder=0, extent=[-100, 100, -100, 100])

    plt.xlabel('X axis mm')
    plt.ylabel('Y axis mm')
    plt.axhline(0, color='gray')
    plt.axvline(0, color='gray')
    plt.title(PLATFORM_NAME)
    if PLATFORM_NAME == "Flying Platform":
        lbl_xoffset = 20
        lbl_yoffset = 20
    else:
         lbl_xoffset = 20
         lbl_yoffset = 20

    for label, x, y in zip(base_labels, bx, by):
        if x > 0 and y < 0:
           h = 'right'
        else:
           h = 'left'
        plt.annotate(
            label,
            xy=(x, y), xytext=(lbl_xoffset, lbl_yoffset),
            textcoords='offset points', ha=h, va='bottom',
            bbox=dict(boxstyle='round,pad=0.2', fc='yellow', alpha=0.5),
            arrowprops=dict(arrowstyle = '->', connectionstyle='arc3,rad=0'))
    for label, x, y in zip(platform_labels, px, py):
        if is_flying_platform:
            h = 'left'
        else:
            if x < 0 and y < 0: h = 'left'
            else: h = 'right'
        if is_flying_platform:  
            if label == "platform1" or label == "platform4" or label == "platform5" :
               offset = (-20, -20)
            else:
               offset = (-20, 20)
        plt.annotate(
            label,
            xy=(x, y), xytext=(offset),
            textcoords='offset points', ha=h, va='bottom',
            bbox=dict(boxstyle='round,pad=0.2', fc='yellow', alpha=0.5),
            arrowprops=dict(arrowstyle = '->', connectionstyle='arc3,rad=0'))

    plt.show()

def plot3d(cfg, platform_transform):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    for i in range(6):
        a = platform_transform[i]
        if i == 5:
            b = platform_transform[0]
        else:
            b = platform_transform[i+1]
        ax.plot( [a[0],b[0]], [a[1],b[1]],[a[2],b[2]], 'yellow')
        
    print("platform type =", cfg.PLATFORM_TYPE)
    if cfg.PLATFORM_TYPE == "SLIDER":
        ax.plot([cfg.center_to_inner_joint,cfg.center_to_inner_joint],[0,-cfg.joint_max_offset],[0,0],'black')
        ax.plot([cfg.center_to_outer_joint,cfg.center_to_outer_joint],[0,cfg.joint_max_offset],[0,0], 'black')


    for i in range(6):
        a = platform_transform[i]
        b = cfg.BASE_POS[i]
        ax.plot( [a[0],b[0]], [a[1],b[1]],[a[2],b[2]], label = str(i))
        ax.legend()


    ax.set_xlabel('X Movement')
    ax.set_ylabel('Y Movement')
    ax.set_zlabel('Z Movement')
    if cfg.PLATFORM_MID_HEIGHT < 0:
        zlimit = (-cfg.limits_1dof[2] + cfg.PLATFORM_MID_HEIGHT,0)
    else:
        zlimit = (0, cfg.limits_1dof[2] + cfg.PLATFORM_MID_HEIGHT)
    ax.set_zlim3d(zlimit)
    ax.set_title(cfg.PLATFORM_NAME)
    plt.show()