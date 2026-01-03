import vtk
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QSlider, QLabel, QWidget
from PyQt5.QtCore import Qt

def load_raw_data(file_path):
    reader = vtk.vtkNrrdReader()
    reader.SetFileName(file_path)
    reader.Update()
    print(f"Raw data extent: {reader.GetDataExtent()}")
    return reader

def load_vtk_meshes(folder_path):
    vtk_meshes = []
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".vtk"):
            file_path = os.path.join(folder_path, file_name)
            reader = vtk.vtkPolyDataReader()
            reader.SetFileName(file_path)
            reader.Update()
            vtk_meshes.append((reader.GetOutput(), file_name))
    return vtk_meshes

def create_vtk_mesh_actors(vtk_meshes, colors):
    actors = []
    predefined_colors = [
        "Tomato", "Banana", "Mint", "Peacock", "Salmon",
        "Lavender", "Wheat", "Cyan", "Pink", "LimeGreen"
    ]
    for i, (mesh, name) in enumerate(vtk_meshes):
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(mesh)

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        color_name = predefined_colors[i % len(predefined_colors)]
        actor.GetProperty().SetColor(colors.GetColor3d(color_name))
        actor.GetProperty().SetOpacity(0.8) 
        actor.name = name  
        actors.append(actor)
    return actors

def visualize_data(raw_data_reader, vtk_meshes):
    colors = vtk.vtkNamedColors()

    main_renderer = vtk.vtkRenderer()
    render_window = vtk.vtkRenderWindow()
    render_window.AddRenderer(main_renderer)
    interactor = vtk.vtkRenderWindowInteractor()
    interactor.SetRenderWindow(render_window)

    vtk_actors = create_vtk_mesh_actors(vtk_meshes, colors)
    for actor in vtk_actors:
        main_renderer.AddActor(actor)

    data_extent = raw_data_reader.GetDataExtent()

    sagittal = vtk.vtkImageActor()
    sagittal.GetMapper().SetInputConnection(raw_data_reader.GetOutputPort())
    sagittal.SetDisplayExtent(
        (data_extent[0] + data_extent[1]) // 2,  
        (data_extent[0] + data_extent[1]) // 2,
        data_extent[2],
        data_extent[3],
        data_extent[4],
        data_extent[5],
    )

    coronal = vtk.vtkImageActor()
    coronal.GetMapper().SetInputConnection(raw_data_reader.GetOutputPort())
    coronal.SetDisplayExtent(
        data_extent[0],
        data_extent[1],
        (data_extent[2] + data_extent[3]) // 2,  
        (data_extent[2] + data_extent[3]) // 2,
        data_extent[4],
        data_extent[5],
    )

    axial = vtk.vtkImageActor()
    axial.GetMapper().SetInputConnection(raw_data_reader.GetOutputPort())
    axial.SetDisplayExtent(
        data_extent[0],
        data_extent[1],
        data_extent[2],
        data_extent[3],
        (data_extent[4] + data_extent[5]) // 2,  
        (data_extent[4] + data_extent[5]) // 2,
    )

    sagittal.GetProperty().SetColorWindow(1000)
    sagittal.GetProperty().SetColorLevel(500)

    coronal.GetProperty().SetColorWindow(1000)
    coronal.GetProperty().SetColorLevel(500)

    axial.GetProperty().SetColorWindow(1000)
    axial.GetProperty().SetColorLevel(500)

    main_renderer.AddActor(sagittal)
    main_renderer.AddActor(coronal)
    main_renderer.AddActor(axial)

    main_renderer.SetBackground(colors.GetColor3d("SlateGray"))
    main_renderer.ResetCamera()

    render_window.SetSize(1600, 1200)

    interactor.Initialize()
    render_window.Render()

    def keypress_callback(obj, event):
        key = obj.GetKeySym()
        if key == "Right":
            extent = list(sagittal.GetDisplayExtent())
            extent[0] += 1
            extent[1] += 1
            sagittal.SetDisplayExtent(*extent)
        elif key == "Left":
            extent = list(sagittal.GetDisplayExtent())
            extent[0] -= 1
            extent[1] -= 1
            sagittal.SetDisplayExtent(*extent)
        elif key == "Up":
            extent = list(coronal.GetDisplayExtent())
            extent[2] += 1
            extent[3] += 1
            coronal.SetDisplayExtent(*extent)
        elif key == "Down":
            extent = list(coronal.GetDisplayExtent())
            extent[2] -= 1
            extent[3] -= 1
            coronal.SetDisplayExtent(*extent)
        elif key == "z":
            extent = list(axial.GetDisplayExtent())
            extent[4] += 1
            extent[5] += 1
            axial.SetDisplayExtent(*extent)
        elif key == "x":
            extent = list(axial.GetDisplayExtent())
            extent[4] -= 1
            extent[5] -= 1
            axial.SetDisplayExtent(*extent)
        render_window.Render()

    interactor.AddObserver("KeyPressEvent", keypress_callback)

    return render_window, vtk_actors

class OpacityControlApp(QMainWindow):
    def __init__(self, vtk_actors, parent=None):
        super(OpacityControlApp, self).__init__(parent)
        self.vtk_actors = vtk_actors

        self.setWindowTitle("Opacity Control Panel")
        self.setGeometry(100, 100, 400, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        for actor in self.vtk_actors:
            label = QLabel(actor.name)
            slider = QSlider(Qt.Horizontal)
            slider.setMinimum(1)  
            slider.setMaximum(10)  
            slider.setValue(int(actor.GetProperty().GetOpacity() * 10))
            slider.valueChanged.connect(lambda value, a=actor: self.update_opacity(a, value))

            self.layout.addWidget(label)
            self.layout.addWidget(slider)

    def update_opacity(self, actor, value):
        new_opacity = value / 10.0
        actor.GetProperty().SetOpacity(new_opacity)
        print(f"Updated opacity of {actor.name} to {new_opacity:.1f}")
        actor.GetMapper().Update()

if __name__ == "__main__":
    raw_data_file = "C:/Users/Emilia/ucho/inner-ear-2018-02/image-volumes/Ear-CT-256.nrrd"
    vtk_mesh_folder = "C:/Users/Emilia/ucho/inner-ear-2018-02/models"

    raw_data_reader = load_raw_data(raw_data_file)
    vtk_meshes = load_vtk_meshes(vtk_mesh_folder)

    render_window, vtk_actors = visualize_data(raw_data_reader, vtk_meshes)

    app = QApplication([])
    opacity_control = OpacityControlApp(vtk_actors)
    opacity_control.show()

    app.exec_()
