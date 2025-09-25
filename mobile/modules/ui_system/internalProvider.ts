import { UISystemService } from './service';

let __uiSystemServiceSingleton: UISystemService | null = null;

export function internalUiSystemProvider(): UISystemService {
  if (!__uiSystemServiceSingleton) {
    __uiSystemServiceSingleton = new UISystemService();
  }
  return __uiSystemServiceSingleton;
}
