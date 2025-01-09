import { Component } from '@angular/core';
import { DocumentSearchComponent } from './components/table-documents/table-documents.component';
import { FileUploadComponent } from './components/upload-file-button/upload-file-button.component';
import { HttpClientModule } from '@angular/common/http'; // Asegúrate de importar HttpClientModule

@Component({
  selector: 'app-home',
  imports: [DocumentSearchComponent, FileUploadComponent, HttpClientModule],
  templateUrl: './home.component.html',
  styleUrl: './home.component.css'
})
export class HomeComponent {

}
