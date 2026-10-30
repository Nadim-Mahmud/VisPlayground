#include <vtkCamera.h>
#include <vtkColorTransferFunction.h>
#include <vtkFixedPointVolumeRayCastMapper.h>
#include <vtkNamedColors.h>
#include <vtkNew.h>
#include <vtkPiecewiseFunction.h>
#include <vtkRenderWindow.h>
#include <vtkRenderWindowInteractor.h>
#include <vtkRenderer.h>
#include <vtkStructuredPointsReader.h>
#include <vtkVolume.h>
#include <vtkVolumeProperty.h>

#include <vtkStructuredPoints.h>
#include <vtkGPUVolumeRayCastMapper.h>
#include <vtkSmartVolumeMapper.h>
#include <vtkOpenGLGPUVolumeRayCastMapper.h>

#include <vtkTransform.h>
#include <vtkAxesActor.h>
#include <vtkTextActor.h>
#include <vtkTextProperty.h>
#include <vtkCaptionActor2D.h>
#include <vtkOutlineFilter.h>
#include <vtkPolyDataMapper.h>
#include <vtkPNGWriter.h>
#include <vtkWindowToImageFilter.h>
#include <vtkMultiThreader.h>

#include <iostream>
#include <fstream>
#include <string>
#include <cstring>

#include "utility.hpp"

#define OTF_CHAMELEON()\
	opacityTransferFunction->AddPoint(0.0, 0.0);\
  	opacityTransferFunction->AddPoint(0.134375, 0.0);\
  	opacityTransferFunction->AddPoint(0.175, 0.268018);\
  	opacityTransferFunction->AddPoint(0.23125, 0.0);\
  	opacityTransferFunction->AddPoint(0.40625, 0.0);\
  	opacityTransferFunction->AddPoint(1.0, 1.0);
#define CTF_CHAMELEON()\
	colorTransferFunction->AddRGBPoint(0.0, 0.02, 0.3813, 0.9981);\
  	colorTransferFunction->AddRGBPoint(0.142857, 0.02, 0.6188, 0.796);\
  	colorTransferFunction->AddRGBPoint(0.238095, 0.02, 0.757035, 0.603735);\
  	colorTransferFunction->AddRGBPoint(0.404762, 0.493355, 0.961904, 0.111195);\
  	colorTransferFunction->AddRGBPoint(0.5, 0.999529, 0.999519, 0.0134885);\
  	colorTransferFunction->AddRGBPoint(0.952381, 0.798903, 0.0433335, 0.358434);\
  	colorTransferFunction->AddRGBPoint(1.0, 0.6837, 0.05, 0.4139);

#define OTF_FLAME()\
	opacityTransferFunction->AddPoint(0.0, 0.0);\
  	opacityTransferFunction->AddPoint(1.0, 1.0);
#define CTF_FLAME()\
	colorTransferFunction->AddRGBPoint(0.0, 0.18995, 0.07176, 0.23217);\
	colorTransferFunction->AddRGBPoint(0.0755593, 0.25369, 0.26327, 0.65406);\
	colorTransferFunction->AddRGBPoint(0.141587, 0.27691, 0.44145, 0.91328);\
	colorTransferFunction->AddRGBPoint(0.210717, 0.23874, 0.61931, 0.99485);\
	colorTransferFunction->AddRGBPoint(0.309764, 0.09532, 0.84455, 0.79299);\
	colorTransferFunction->AddRGBPoint(0.409599, 0.29042, 0.97403, 0.50321);\
	colorTransferFunction->AddRGBPoint(0.517145, 0.66428, 0.98524, 0.2237);\
	colorTransferFunction->AddRGBPoint(0.619351, 0.91317, 0.83576, 0.22328);\
	colorTransferFunction->AddRGBPoint(0.728105, 0.99517, 0.57549, 0.16412);\
	colorTransferFunction->AddRGBPoint(0.821329, 0.91572, 0.3053, 0.05134);\
	colorTransferFunction->AddRGBPoint(0.914552, 0.73661, 0.12477, 0.00769);\
	colorTransferFunction->AddRGBPoint(0.996117, 0.49321, 0.01963, 0.00955);\
	colorTransferFunction->AddRGBPoint(1.0, 0.4796, 0.01583, 0.01055);

#define OTF_MIRANDA()\
	opacityTransferFunction->AddPoint(0.0, 1.0);\
  	opacityTransferFunction->AddPoint(0.26, 0.0);\
  	opacityTransferFunction->AddPoint(0.42, 0.0);\
  	opacityTransferFunction->AddPoint(0.52, 0.6);\
  	opacityTransferFunction->AddPoint(0.62, 0.0);\
  	opacityTransferFunction->AddPoint(0.76, 0.0);\
  	opacityTransferFunction->AddPoint(1.0, 1.0);
#define CTF_MIRANDA()\
	colorTransferFunction->AddRGBPoint(0.0, 0.0, 0.9, 0.9);\
  	colorTransferFunction->AddRGBPoint(0.45, 0.0, 0.0, 1.0);\
  	colorTransferFunction->AddRGBPoint(0.5, 0.0, 0.0, 0.5);\
  	colorTransferFunction->AddRGBPoint(0.55, 1.0, 0.0, 0.0);\
  	colorTransferFunction->AddRGBPoint(1.0, 1.0, 1.0, 0.0);

#define OTF_BEECHNUT()\
	opacityTransferFunction->AddPoint(0.0, 0.0);\
  	opacityTransferFunction->AddPoint(0.245059, 0.0);\
  	opacityTransferFunction->AddPoint(0.249012, 0.195946);\
  	opacityTransferFunction->AddPoint(0.252964, 0.0);\
  	opacityTransferFunction->AddPoint(0.264822, 0.0);\
  	opacityTransferFunction->AddPoint(0.278656, 0.394144);\
  	opacityTransferFunction->AddPoint(0.294466, 0.0);\
  	opacityTransferFunction->AddPoint(0.310277, 0.0);\
  	opacityTransferFunction->AddPoint(0.320158, 0.637387);\
  	opacityTransferFunction->AddPoint(1.0, 1.0);
#define CTF_BEECHNUT()\
	colorTransferFunction->AddRGBPoint(0.0, 0.02, 0.3813, 0.9981);\
  	colorTransferFunction->AddRGBPoint(0.225296, 0.02, 0.72, 0.6574);\
  	colorTransferFunction->AddRGBPoint(0.26087, 0.999529, 0.999519, 0.0134885);\
  	colorTransferFunction->AddRGBPoint(0.288538, 1.0, 0.212, 0.988);\
  	colorTransferFunction->AddRGBPoint(0.316206, 0.62, 0.118, 0.988);\
  	colorTransferFunction->AddRGBPoint(1.0, 0.6837, 0.05, 0.4139);


int view_size = 0;
std::vector<std::vector<double>> view_list;

class vtkTimerCallback2 : public vtkCommand
{
public:
  vtkTimerCallback2() = default;
  ~vtkTimerCallback2() = default;

  int timerId = 0;
  static vtkTimerCallback2* New()
  {
    vtkTimerCallback2* cb = new vtkTimerCallback2;
    cb->TimerCount = 0;
    return cb;
  }
  virtual void Execute(vtkObject* caller, unsigned long eventId,
                       void* vtkNotUsed(callData))
  {
    vtkRenderWindowInteractor* iren =
        dynamic_cast<vtkRenderWindowInteractor*>(caller);
    if (vtkCommand::TimerEvent == eventId)
    {
      ++this->TimerCount;
    }
    std::cout << "TimerCount: " << TimerCount << std::endl; //TimerCount starts from 1
	std::cout << "view_size: "  << view_size << std::endl;
	std::cout << "view_list size: " << view_list.size() << std::endl;
#if 1
    if (TimerCount < view_size + 1) // image index from 1 to view_size
    // if (TimerCount < 11) // image index from 1 to view_size
    {
		camera->SetPosition(view_list.at(TimerCount - 1).at(0),
						    view_list.at(TimerCount - 1).at(1),
							view_list.at(TimerCount - 1).at(2));
		camera->SetFocalPoint(view_list.at(TimerCount - 1).at(3),
						      view_list.at(TimerCount - 1).at(4),
							  view_list.at(TimerCount - 1).at(5));
		camera->SetViewUp(view_list.at(TimerCount - 1).at(6),
						  view_list.at(TimerCount - 1).at(7),
					      view_list.at(TimerCount - 1).at(8));
		printCamera(camera);
#if 1 
      // Screenshot
      vtkNew<vtkWindowToImageFilter> windowToImageFilter;
      windowToImageFilter->SetInput(iren->GetRenderWindow());
      windowToImageFilter->SetScale(1); // image quality
      // windowToImageFilter->SetInputBufferTypeToRGBA(); // also record the alpha
      windowToImageFilter->SetInputBufferTypeToRGB(); // also record the alpha
      windowToImageFilter->ReadFrontBufferOff();       // read from the back buffer
      // windowToImageFilter->Update();

      vtkNew<vtkPNGWriter> writer;
      std::string fileName = "screenShot/" + std::to_string(TimerCount) + ".png";
      writer->SetFileName(fileName.c_str());
      writer->SetInputConnection(windowToImageFilter->GetOutputPort());
      writer->Write();
      std::cout << "=======Saving Done!" << endl;
#endif
      // iren->GetRenderWindow()->Render();

      // iren->GetRenderWindow()->Render();
    }
    else
    {
      std::cout << "Timer distroied" << std::endl;
      iren->DestroyTimer();
    }
#endif
  }

private:
  int TimerCount = 0;

public:
  // vtkActor* actor;
  vtkVolume* volume;
  vtkCamera* camera;
};
int main(int argc, char* argv[])
{
	vtkMultiThreader::SetGlobalMaximumNumberOfThreads(1);
	if (argc < 2)
	{
    	std::cout << "Usage: " << argv[0] << " ironProt.vtk" << std::endl;
    	return EXIT_FAILURE;
	}


	std::string view_file_name = argv[2];
	int block_size, ray_size, sample_size, up_size;
	getSizes(view_file_name, block_size, ray_size, sample_size, up_size); 
	std::cout << block_size << ", " << ray_size << ", " << sample_size << ", " << up_size << std::endl;
	view_size = block_size*ray_size*sample_size*up_size;
  	// Read views
  	double views[block_size][ray_size][sample_size][up_size][9];
	std::ifstream file(view_file_name, std::ios::binary);
    // Check if the file was opened successfully
    if (!file) {
        std::cerr << "Error opening file" << std::endl;
        return 1;
    }
	
    // Read the binary data into the vector
	int data_size = block_size*ray_size*sample_size*up_size*9;
	double data[data_size];
    file.read(reinterpret_cast<char*>(data), data_size*sizeof(double));
    file.close();
	// Array data into view tensor
	for (int i = 0; i < block_size; i++) {
		for (int j = 0; j < ray_size; j++) {
			for (int k = 0; k < sample_size; k++) {
				for (int l = 0; l < up_size; l++) {
					int index = i*ray_size*sample_size*up_size +
								j*sample_size*up_size +
								k*up_size + l;
					std::memcpy(&(views[i][j][k][l][0]),
								&(data[index*9]),
								9*sizeof(double));
					std::vector<double> view;
					for (int m = 0; m < 9; m++) {
						view.push_back(data[index*9 + m]);
					}
					view_list.push_back(view);
				}
			}
		}
	}
	std::cout << "position: " << views[0][0][0][0][0] << ", " << views[0][0][0][0][1] << ", " << views[0][0][0][0][2] << std::endl;
	std::cout << "focal: " << views[0][0][0][0][3] << ", " << views[0][0][0][0][4] << ", " << views[0][0][0][0][5] << std::endl;
	std::cout << "up: " << views[0][0][0][0][6] << ", " << views[0][0][0][0][7] << ", " << views[0][0][0][0][8] << std::endl;
	

	// Create the standard renderer, render window and interactor
  	vtkNew<vtkNamedColors> colors;
  	vtkNew<vtkRenderer> ren1;

  	vtkNew<vtkRenderWindow> renWin;
 	renWin->AddRenderer(ren1);

 	vtkNew<vtkRenderWindowInteractor> iren;
  	iren->SetRenderWindow(renWin);

  	// Create the reader for the data
  	vtkNew<vtkStructuredPointsReader> reader;
  	reader->SetFileName(argv[1]);
  	reader->Update();

  	double r[2];
  	reader->GetOutput()->GetScalarRange(r);
  	std::cout << "min: " << r[0] << std::endl;
  	std::cout << "max: " << r[1] << std::endl;


  	// Create transfer mapping scalar value to opacity
  	// vtkNew<vtkPiecewiseFunction> opacityTransferFunction;
  	vtkSmartPointer<vtkPiecewiseFunction> opacityTransferFunction = vtkSmartPointer<vtkPiecewiseFunction>::New();
	OTF_CHAMELEON();
	// OTF_FLAME();
	// OTF_MIRANDA();
	// OTF_BEECHNUT();
#if 0
  	opacityTransferFunction->AddPoint(0.0, 0.0);
  	opacityTransferFunction->AddPoint(1.0, 1.0);
#endif
  // Create transfer mapping scalar value to color
  	vtkNew<vtkColorTransferFunction> colorTransferFunction;
	CTF_CHAMELEON();
	// CTF_FLAME();
	// CTF_MIRANDA();
	// CTF_BEECHNUT();
#if 0
  	colorTransferFunction->AddRGBPoint(0.0, 1.0, 0.0, 0.0);
  	colorTransferFunction->AddRGBPoint(0.5, 0.0, 1.0, 0.0);
  	colorTransferFunction->AddRGBPoint(1.0, 0.0, 0.0, 1.0);
#endif

  	// The property describes how the data will look
  	vtkNew<vtkVolumeProperty> volumeProperty;
  	volumeProperty->SetColor(colorTransferFunction);
  	volumeProperty->SetScalarOpacity(opacityTransferFunction);
  	// volumeProperty->ShadeOn();
  	volumeProperty->SetInterpolationTypeToLinear();

  	// The mapper / ray cast function know how to render the data
  	vtkNew<vtkFixedPointVolumeRayCastMapper> volumeMapper;
  	// vtkNew<vtkGPUVolumeRayCastMapper> volumeMapper; // irrelevant to sample distance
  	// vtkNew<vtkOpenGLGPUVolumeRayCastMapper> volumeMapper; // irrelevant to sample distance
  	// vtkNew<vtkSmartVolumeMapper> volumeMapper; // irrelevant to sample distance
  	volumeMapper->SetInputConnection(reader->GetOutputPort());
  	std::cout << "sample distance: " << volumeMapper->GetSampleDistance() << std::endl;
  	volumeMapper->SetSampleDistance(0.1); // 0.1 works best for 256 cube data with 1 spacing
  	// volumeMapper->SetSampleDistance(0.01); // 0.01 only used for timing test
  	std::cout << "sample distance: " << volumeMapper->GetSampleDistance() << std::endl;
  	volumeMapper->SetBlendModeToComposite();

  	// The volume holds the mapper and the property and
  	// can be used to position/orient the volume
  	vtkNew<vtkVolume> volume;
  	volume->SetMapper(volumeMapper);
  	volume->SetProperty(volumeProperty);

	// turnOnAxis(volume, ren1);
	// turnOnBoundingBox(reader, ren1);

  	ren1->AddVolume(volume);
  	// ren1->SetBackground(colors->GetColor3d("Wheat").GetData());
  	ren1->SetBackground(0, 0, 0);
  	// ren1->GetActiveCamera()->Azimuth(45);
  	// ren1->GetActiveCamera()->Elevation(30);

  	ren1->ResetCameraClippingRange();
  	ren1->ResetCamera();
  	printCamera(ren1->GetActiveCamera());
  	double r_min = 73.61215932167728;
  	double r_max = 772.9276728776115; // 662.5094338950955; // 441.6729559300637;
  	ren1->GetActiveCamera()->SetPosition(views[0][0][0][3][0],
				  					     views[0][0][0][3][1],
									     views[0][0][0][3][2]);
  	ren1->GetActiveCamera()->SetFocalPoint(views[0][0][0][3][3],
				  					   	   views[0][0][0][3][4],
									       views[0][0][0][3][5]);
  	ren1->GetActiveCamera()->SetViewUp(views[0][0][0][3][6],
				  					   views[0][0][0][3][7],
									   views[0][0][0][3][8]);
  	ren1->GetActiveCamera()->SetViewAngle(30);
  	ren1->GetActiveCamera()->SetClippingRange(0.1, 1000);
  	printCamera(ren1->GetActiveCamera());
  
  	// renWin->SetSize(1024, 1024);
  	// renWin->SetSize(512, 512);
  	renWin->SetSize(256, 256);
  	// renWin->SetSize(64, 64);
  	renWin->SetWindowName("Rendering Result");
  	renWin->Render();

#if 1 // starts animation
    // Initialize must be called prior to creating timer events.
    iren->Initialize();
    // Sign up to receive TimerEvent
    vtkNew<vtkTimerCallback2> cb;
    cb->volume = volume;
	cb->camera = ren1->GetActiveCamera();
    iren->AddObserver(vtkCommand::TimerEvent, cb);
    int timerId = iren->CreateRepeatingTimer(1000); // ms
    cb->timerId = timerId;
#endif

  	iren->Start();

  	return EXIT_SUCCESS;
}
