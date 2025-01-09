import { TestBed } from '@angular/core/testing';

import { UploadFileTsService } from './upload-file.ts.service';

describe('UploadFileTsService', () => {
  let service: UploadFileTsService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(UploadFileTsService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
