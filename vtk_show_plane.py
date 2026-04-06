import vtk
import numpy as np
from ap200_interface import get_rt_now

# Type alias 方便你使用
Vector3D = np.ndarray
Matrix3x3 = np.ndarray

def combine_transform(
    R1: Matrix3x3, T1: Vector3D,
    R2: Matrix3x3, T2: Vector3D
) -> tuple[Matrix3x3, Vector3D]:
    """
    合并两个刚体变换：先执行 (R1,T1)，再执行 (R2,T2)
    返回等效的总变换 (R0, T0)

    数学公式：
    R0 = R2 @ R1
    T0 = R2 @ T1 + T2
    """
    R0 = R2 @ R1
    T0 = R2 @ T1 + T2
    return R0, T0


class STLPlaneViewer:
    def __init__(self):
        self.renderer = vtk.vtkRenderer()
        self.render_window = vtk.vtkRenderWindow()
        self.render_window.AddRenderer(self.renderer)
        self.interactor = vtk.vtkRenderWindowInteractor()
        self.interactor.SetRenderWindow(self.render_window)
        self.interactor.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())

        self.stl_actor = None
        self.plane_actor = None
        self.plane_source = None

        # ======================
        # 平面初始位姿（仅平面使用）
        # ======================
        self.initial_plane_transform = None

        self.renderer.SetBackground(0.2, 0.2, 0.2)

        # 角落坐标系
        self.axes_widget = vtk.vtkAxesActor()
        self.axes_widget.SetTotalLength(0.1, 0.1, 0.1)
        self.orientation_marker = vtk.vtkOrientationMarkerWidget()
        self.orientation_marker.SetOrientationMarker(self.axes_widget)
        self.orientation_marker.SetInteractor(self.interactor)
        self.orientation_marker.SetViewport(0.0, 0.0, 0.2, 0.2)
        self.orientation_marker.SetEnabled(1)
        self.orientation_marker.InteractiveOff()

    def load_stl(self, stl_path: str) -> None:
        reader = vtk.vtkSTLReader()
        reader.SetFileName(stl_path)
        reader.Update()
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(reader.GetOutputPort())
        self.stl_actor = vtk.vtkActor()
        self.stl_actor.SetMapper(mapper)
        self.stl_actor.GetProperty().SetColor(0.7, 0.7, 0.8)
        self.stl_actor.GetProperty().SetOpacity(1.0)
        self.renderer.AddActor(self.stl_actor)

    def create_plane(self, center: Vector3D, normal: Vector3D, size: float = 100.0) -> None:
        center = np.asarray(center, dtype=np.float64)
        normal = np.asarray(normal, dtype=np.float64)
        normal = normal / np.linalg.norm(normal)

        self.plane_source = vtk.vtkPlaneSource()
        self.plane_source.SetCenter(center)
        self.plane_source.SetNormal(normal)
        self.plane_source.SetXResolution(20)
        self.plane_source.SetYResolution(20)
        self.plane_source.SetPoint1(center[0] + size, center[1], center[2])
        self.plane_source.SetPoint2(center[0], center[1] + size, center[2])
        self.plane_source.Update()

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(self.plane_source.GetOutputPort())
        self.plane_actor = vtk.vtkActor()
        self.plane_actor.SetMapper(mapper)
        self.plane_actor.GetProperty().SetColor(1.0, 0.2, 0.2)
        self.plane_actor.GetProperty().SetOpacity(1.0)
        self.renderer.AddActor(self.plane_actor)

    # ======================
    # 保存当前平面姿态为初始姿态
    # ======================
    def save_initial_plane_pose(self):
        if self.plane_actor:
            t = self.plane_actor.GetUserTransform()
            if not t:
                t = vtk.vtkTransform()
                t.Identity()
            self.initial_plane_transform = vtk.vtkTransform()
            self.initial_plane_transform.DeepCopy(t)

    # ======================
    # 通用设置变换
    # ======================
    def set_actor_transform(self, actor, rot, trans):
        transform = vtk.vtkTransform()
        transform.Identity()
        transform.Translate(*trans)
        mat = vtk.vtkMatrix4x4()
        mat.Identity()
        for i in range(3):
            for j in range(3):
                mat.SetElement(i, j, rot[i, j])
        transform.Concatenate(mat)
        actor.SetUserTransform(transform)
        self.render_window.Render()

    # ======================
    # ✅ 平面：基于【初始姿态】设置
    # ======================
    def set_plane_transform(self, rotation: Matrix3x3, translation: Vector3D):
        if not self.plane_actor or self.initial_plane_transform is None:
            return

        # 新的小变换
        new_t = vtk.vtkTransform()
        new_t.Identity()
        new_t.Translate(*translation)
        mat = vtk.vtkMatrix4x4()
        mat.Identity()
        for i in range(3):
            for j in range(3):
                mat.SetElement(i, j, rotation[i, j])
        new_t.Concatenate(mat)

        # 最终 = 初始位姿 × 新变换
        total = vtk.vtkTransform()
        total.Identity()
        total.Concatenate(self.initial_plane_transform)
        total.Concatenate(new_t)

        self.plane_actor.SetUserTransform(total)
        self.render_window.Render()

    # ======================
    # STL：直接设置，不受初始位姿影响
    # ======================
    def set_stl_transform(self, rotation: Matrix3x3, translation: Vector3D):
        if self.stl_actor:
            self.set_actor_transform(self.stl_actor, rotation, translation)

    def show(self):
        camera = self.renderer.GetActiveCamera()

        # ---------------------------
        # 你的相机坐标系要求
        # ---------------------------
        camera.SetPosition(0, 0, 0)          # 相机在原点
        camera.SetFocalPoint(0, 0, +500)     # 看向 Z+
        camera.SetViewUp(0, -1, 0)            # Y 向下

        # ---------------------------
        # 正交投影 + 显示范围 -200 ~ 200
        # ---------------------------
        camera.SetClippingRange(0.1, 10000000.0)

        self.render_window.SetSize(1000, 800)
        self.render_window.SetWindowName("STL + Plane")
        self.interactor.Initialize()
        self.render_window.Render()
        self.interactor.Start()

def get_rotation_matrix(rad_x: float, rad_y: float, rad_z: float) -> Matrix3x3:
    cx, sx = np.cos(rad_x), np.sin(rad_x)
    cy, sy = np.cos(rad_y), np.sin(rad_y)
    cz, sz = np.cos(rad_z), np.sin(rad_z)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]], dtype=np.float64)
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]], dtype=np.float64)
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]], dtype=np.float64)
    return Rz @ Ry @ Rz

# ==============================
# Test Code
# ==============================
if __name__ == "__main__":

    STL_FILE_PATH = "BONE-1.new.stl"
    PLANE_CENTER = [0, 0, 0]
    PLANE_NORMAL = [0, 0, 1]

    viewer = STLPlaneViewer()
    viewer.load_stl(STL_FILE_PATH)
    viewer.create_plane(center=PLANE_CENTER, normal=PLANE_NORMAL, size=80)

    # 1. 设置初始位姿
    init_rot = get_rotation_matrix(0, np.deg2rad(45), 0)
    init_trans = np.array([-50, -20, -20])
    viewer.set_plane_transform(init_rot, init_trans)

    # 2. ✅ 保存为平面初始位姿
    viewer.save_initial_plane_pose()

    # 3. 每秒更新：基于初始位姿叠加
    def update_callback(obj, event):
        delta_rot, delta_trans = get_rt_now()
        if delta_rot is None or delta_trans is None:
            return
        r0, t0 = combine_transform(
            init_rot, init_trans,
            delta_rot, delta_trans
        )
        print(delta_rot, delta_trans)
        viewer.set_plane_transform(r0, t0)
        viewer.set_stl_transform(delta_rot, delta_trans)

    iren = viewer.interactor
    iren.Initialize()
    iren.AddObserver("TimerEvent", update_callback)
    iren.CreateRepeatingTimer(1)

    viewer.show()