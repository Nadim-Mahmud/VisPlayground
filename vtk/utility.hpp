#include <vtkCamera.h>
#include <iostream>
#include <fstream>
#include <string>
#include <cstring>

void printCamera(vtkCamera *camera) {
  double positions[3];
  camera->GetPosition(positions);
  double focal[3];
  camera->GetFocalPoint(focal);
  double viewUp[3];
  camera->GetViewUp(viewUp);
  std::cout << "-------Camera Parameters-------" << std::endl;
  std::cout << "position: " << positions[0] << ", " << positions[1] << ", " << positions[2] << std::endl;
  std::cout << "focal: " << focal[0] << ", " << focal[1] << ", " << focal[2] << std::endl;
  std::cout << "up: " << viewUp[0] << ", " << viewUp[1] << ", " << viewUp[2] << std::endl;
  std::cout << "camera view angle: " << camera->GetViewAngle() << std::endl;
  double cr[2];
  camera->GetClippingRange(cr);
  std::cout << "camera clipping Range: " << cr[0] << ", " << cr[1] << std::endl;
}

std::vector<std::string> splitString(const std::string& str, char delimiter) {
    std::vector<std::string> tokens;
    std::string token;
    std::stringstream ss(str);
    
    while (std::getline(ss, token, delimiter)) {
        tokens.push_back(token);
    }
    
    // Handle the case where the string ends with a delimiter
    if (!str.empty() && str.back() == delimiter) {
        tokens.push_back("");
    }
    
    return tokens;
}
void getSizes(std::string view_file_name,
			  int &block_size,
			  int &ray_size,
			  int &sample_size,
			  int &up_size) {
  	// std::cout << "view file name: " << view_file_name << std::endl;
  	view_file_name.erase(view_file_name.length() - 4, 4);
  	// Find the last '/'
	int start = 0;
  	for (int i = view_file_name.length() - 1; i >=0; i--) {
  		// std::cout << i << ": " << view_file_name[i] << std::endl;
		if (view_file_name[i] == '/') {
			start = i + 1;
			break;
		}
  	}
	view_file_name = view_file_name.substr(start);
	// std::cout << "extracted file name: " << view_file_name << std::endl;

	std::vector<std::string> result = splitString(view_file_name, '_');
	block_size = std::stoi(result.at(1));
	ray_size = std::stoi(result.at(2));
	sample_size = std::stoi(result.at(3));
	up_size = std::stoi(result.at(4));
}

int readViews(double *****views,
			   std::string view_file,
			   int block_size,
			   int ray_size,
			   int sample_size,
			   int up_size) {
	std::ifstream file(view_file, std::ios::binary);

    // Check if the file was opened successfully
    if (!file) {
        std::cerr << "Error opening file" << std::endl;
        return 1;
    }

    // Read the binary data into the vector
	int data_size = block_size*ray_size*sample_size*up_size*9;
	double data[data_size];
    file.read(reinterpret_cast<char*>(data), data_size*sizeof(double));

    // Close the file
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
				}
			}
		}
	}
	return 0;
}

void turnOnAxis(vtkVolume *volume, vtkRenderer *ren1) {
	vtkNew<vtkTransform> transform;
    vtkNew<vtkAxesActor> axes;
    double l[3];
    l[0] = (volume->GetBounds()[1] - volume->GetBounds()[0]) * 1.5;
    l[1] = (volume->GetBounds()[3] - volume->GetBounds()[2]) * 1.5;
    l[2] = (volume->GetBounds()[5] - volume->GetBounds()[4]) * 1.5;
    axes->SetTotalLength(l);
    axes->SetConeRadius(0.1);
    vtkSmartPointer<vtkTextProperty> tprop = vtkSmartPointer<vtkTextProperty>::New();
    tprop->ItalicOn();
    tprop->ShadowOn();
    tprop->SetFontFamilyToTimes();
    // std::cout << tprop->GetFontSize();
    tprop->SetFontSize(18);
    axes->GetXAxisCaptionActor2D()->GetTextActor()->SetTextScaleMode(vtkTextActor::TEXT_SCALE_MODE_NONE);
    axes->GetXAxisCaptionActor2D()->GetTextActor()->GetTextProperty()->SetFontSize(30);
    axes->GetYAxisCaptionActor2D()->GetTextActor()->SetTextScaleMode(vtkTextActor::TEXT_SCALE_MODE_NONE);
    axes->GetYAxisCaptionActor2D()->GetTextActor()->GetTextProperty()->SetFontSize(30);
    axes->GetZAxisCaptionActor2D()->GetTextActor()->SetTextScaleMode(vtkTextActor::TEXT_SCALE_MODE_NONE);
    axes->GetZAxisCaptionActor2D()->GetTextActor()->GetTextProperty()->SetFontSize(30);
    ren1->AddActor(axes);

}

void turnOnBoundingBox(vtkStructuredPointsReader *reader, vtkRenderer *ren1) {
	double bounds[6];
    reader->GetOutput()->GetBounds(bounds);
    // Create an outline filter to generate the bounding box
    vtkSmartPointer<vtkOutlineFilter> outlineFilter = vtkSmartPointer<vtkOutlineFilter>::New();
    outlineFilter->SetInputConnection(reader->GetOutputPort());
    outlineFilter->Update();
    // Create a mapper for the outline
    vtkSmartPointer<vtkPolyDataMapper> outlineMapper = vtkSmartPointer<vtkPolyDataMapper>::New();
    outlineMapper->SetInputConnection(outlineFilter->GetOutputPort());
    // Create an actor for the outline 
    vtkSmartPointer<vtkActor> outlineActor = vtkSmartPointer<vtkActor>::New();
    outlineActor->SetMapper(outlineMapper);
  	ren1->AddActor(outlineActor);
}


